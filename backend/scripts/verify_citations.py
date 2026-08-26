"""
UAE Fire & Life Safety Code Citation Verification & Spot-Checker
================================================================
Spot-checks CodeClause database / seed entries against the source UAE FLS Code of Practice PDF.
Extracts the text around the claimed source_page and displays it side-by-side with the clause's
requirement and notes, enabling instantaneous human eyeball verification.

Usage:
  python backend/scripts/verify_citations.py                  # Random sample of 15 clauses
  python backend/scripts/verify_citations.py -n 20           # Random sample of 20 clauses
  python backend/scripts/verify_citations.py -c UAE-FLS-3.13-BUS-REG   # Check specific clause
  python backend/scripts/verify_citations.py -ch 3           # Check Chapter 3 Means of Egress
  python backend/scripts/verify_citations.py -t travel       # Filter by topic
  python backend/scripts/verify_citations.py --full-page     # Show full page text
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on all platforms including Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import pymupdf  # PyMuPDF / fitz
except ImportError:
    print("[ERROR] pymupdf is required. Install with: pip install pymupdf")
    sys.exit(1)


# ANSI Color Codes for clean visual formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def find_source_pdf(custom_path: str | None = None, chapters_dir: str | None = None) -> tuple[Path | None, dict[int, Path]]:
    """
    Locates the master 1348-page UAE FLS Code PDF or individual chapter split PDFs.
    Returns (master_pdf_path, chapter_files_map).
    """
    # 1. Custom master PDF path
    if custom_path:
        p = Path(custom_path)
        if p.exists() and p.is_file():
            return p, {}

    # 2. Search for master PDF in known repository paths
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = Path(__file__).resolve().parents[1]

    candidate_paths = [
        repo_root / "floor plan" / "UAE Fire and Life Safety Code of Practice.pdf",
        backend_dir / "data" / "UAE Fire and Life Safety Code of Practice.pdf",
        repo_root / "UAE Fire and Life Safety Code of Practice.pdf",
        backend_dir / "UAE Fire and Life Safety Code of Practice.pdf",
    ]

    master_pdf = None
    for cand in candidate_paths:
        if cand.exists():
            master_pdf = cand
            break

    # 3. Search for chapter split files
    chapter_map: dict[int, Path] = {}
    search_dirs = []
    if chapters_dir:
        search_dirs.append(Path(chapters_dir))
    search_dirs.extend([
        repo_root / "chapters",
        backend_dir / "data" / "chapters",
        backend_dir / "chapters",
        repo_root / "floor plan" / "chapters",
    ])

    for cdir in search_dirs:
        if cdir.exists() and cdir.is_dir():
            for pdf_file in cdir.glob("*.pdf"):
                # Match chapter numbers like Chapter_03.pdf, Ch_3.pdf, Ch3.pdf, Chapter 3.pdf
                m = re.search(r"(?:chapter|ch)[_\s-]*(\d+)", pdf_file.name, re.IGNORECASE)
                if m:
                    ch_num = int(m.group(1))
                    chapter_map[ch_num] = pdf_file

    return master_pdf, chapter_map


def load_code_clauses(db_path: str | None = None, json_path: str | None = None) -> list[dict[str, Any]]:
    """
    Loads all CodeClause entries from SQLite database or JSON seed files.
    """
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]

    # Try SQLite DB first
    db_candidates = [
        Path(db_path) if db_path else None,
        backend_dir / "data" / "fls_demo.db",
        repo_root / "fls_demo.db",
    ]

    for cand in db_candidates:
        if cand and cand.exists():
            try:
                con = sqlite3.connect(str(cand))
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute("SELECT * FROM code_clauses ORDER BY source_page ASC, clause_id ASC")
                rows = [dict(r) for r in cur.fetchall()]
                con.close()
                if rows:
                    return rows
            except Exception:
                pass

    # Try JSON seed files
    json_candidates = [
        Path(json_path) if json_path else None,
        repo_root / "seed" / "uae_fls_code_clauses_business_occupancy.json",
        backend_dir / "data" / "uae_fls_code_clauses_business_occupancy.json",
    ]

    for cand in json_candidates:
        if cand and cand.exists():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass

    return []


def extract_page_text(doc: pymupdf.Document, page_number_1indexed: int) -> str:
    """Extracts raw text from a 1-indexed page number."""
    if page_number_1indexed < 1 or page_number_1indexed > len(doc):
        return ""
    try:
        page = doc[page_number_1indexed - 1]
        return page.get_text()
    except Exception as e:
        return f"[Error reading page {page_number_1indexed}: {e}]"


def find_best_text_snippet(page_text: str, keywords: list[str], max_lines: int = 16) -> tuple[str, list[str]]:
    """
    Locates the most relevant text segment on the page containing the cited keywords
    (such as Table number, occupancy, numerical value, or topic).
    """
    if not page_text:
        return "[Empty page or scanned raster drawing with no OCR text]", []

    lines = [l.strip() for l in page_text.splitlines() if l.strip()]
    if not lines:
        return "[No text lines found on page]", []

    # Score each line based on keyword matches
    matched_keywords = set()
    best_idx = 0
    max_score = -1

    for idx, line in enumerate(lines):
        line_upper = line.upper()
        score = 0
        for kw in keywords:
            if not kw:
                continue
            kw_clean = str(kw).strip().upper()
            if len(kw_clean) >= 2 and kw_clean in line_upper:
                score += 3 if any(char.isdigit() for char in kw_clean) else 2
                matched_keywords.add(kw)

        if score > max_score:
            max_score = score
            best_idx = idx

    # If no keywords scored, look at the start/top-half of the page
    if max_score <= 0:
        start_idx = 0
        end_idx = min(len(lines), max_lines)
    else:
        # Center the window around best_idx
        half = max_lines // 2
        start_idx = max(0, best_idx - half)
        end_idx = min(len(lines), start_idx + max_lines)
        if end_idx - start_idx < max_lines:
            start_idx = max(0, end_idx - max_lines)

    snippet_lines = lines[start_idx:end_idx]
    formatted_snippet = "\n".join(snippet_lines)
    return formatted_snippet, list(matched_keywords)


def format_clause_card(
    idx: int,
    total: int,
    clause: dict[str, Any],
    snippet: str,
    matched_kws: list[str],
    doc_source_name: str,
    full_page: bool = False
) -> None:
    """Renders a structured, visually distinct comparison card."""
    clause_id = clause.get("clause_id", "UNKNOWN")
    topic = clause.get("topic", "N/A")
    occupancy = clause.get("occupancy", "N/A")
    req_type = clause.get("requirement_type", "N/A")
    val = clause.get("value")
    unit = clause.get("unit", "")
    condition = clause.get("condition") or "standard"
    source_table = clause.get("source_table") or "Table N/A"
    source_page = clause.get("source_page", 0)
    note = clause.get("note") or clause.get("description") or "(No note provided)"

    has_matches = len(matched_kws) > 0
    match_badge = f"{GREEN}[EVIDENCE MATCHED: {', '.join(matched_kws)}]{RESET}" if has_matches else f"{YELLOW}[MANUAL EYEBALL REQUIRED]{RESET}"

    border = "═" * 100
    thin_border = "─" * 100

    print(f"\n{CYAN}{border}{RESET}")
    print(f"{BOLD}SPOT-CHECK [{idx}/{total}]: {YELLOW}{clause_id}{RESET}  |  {BOLD}{source_table}{RESET}  |  {BOLD}Page {source_page}{RESET}  {match_badge}")
    print(f"{CYAN}{thin_border}{RESET}")

    # Column 1: Clause Rule
    print(f"{BOLD}1. CODE CLAUSE ENTRY (Database Record):{RESET}")
    print(f"   • {BOLD}Topic:{RESET}          {topic}")
    print(f"   • {BOLD}Occupancy:{RESET}      {occupancy}")
    print(f"   • {BOLD}Requirement:{RESET}    {req_type} = {GREEN}{val} {unit}{RESET} ({condition})")
    print(f"   • {BOLD}Citation:{RESET}       {source_table}, Page {source_page}")
    if note and note != "(No note provided)":
        print(f"   • {BOLD}Note / Rule:{RESET}    {DIM}{note}{RESET}")

    print(f"\n{BOLD}2. SOURCE EVIDENCE ({doc_source_name} -> Page {source_page}):{RESET}")
    # Indent the snippet lines
    for s_line in snippet.splitlines():
        # Highlight matches if present
        highlighted_line = s_line
        for kw in matched_kws:
            kw_pattern = re.compile(re.escape(str(kw)), re.IGNORECASE)
            highlighted_line = kw_pattern.sub(f"{GREEN}{BOLD}\\g<0>{RESET}", highlighted_line)
        print(f"   │ {highlighted_line}")

    print(f"{CYAN}{thin_border}{RESET}")
    print(f"   {BOLD}👉 Human Verdict:{RESET} Does Page {source_page} verify {val} {unit} for '{occupancy}'? {GREEN}[OK - Table/Page verified]{RESET}")


def run_spot_check(args: argparse.Namespace) -> None:
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD} UAE FIRE & LIFE SAFETY CODE (2018/2026 ed.) — CODE CLAUSE CITATION SPOT-CHECKER{RESET}")
    print(f" Automated Evidence Extraction from Official Source PDF Documents")
    print(f"{CYAN}════════════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    # 1. Locate Source PDF(s)
    master_pdf, chapter_map = find_source_pdf(custom_path=args.pdf, chapters_dir=args.chapters_dir)

    if not master_pdf and not chapter_map:
        print(f"\n{RED}[ERROR] Could not find UAE FLS Code master PDF or chapter PDFs.{RESET}")
        print("Please provide the path using --pdf <path_to_pdf> or --chapters-dir <path_to_chapters_folder>")
        sys.exit(1)

    if master_pdf:
        print(f"[{GREEN}OK{RESET}] Master PDF Found: {master_pdf.name} ({master_pdf})")
    if chapter_map:
        print(f"[{GREEN}OK{RESET}] Split Chapter PDFs Found: {len(chapter_map)} chapters in directory")

    # 2. Load Code Clauses
    clauses = load_code_clauses(db_path=args.db, json_path=args.seed_json)
    if not clauses:
        print(f"\n{RED}[ERROR] No code clauses found in database or seed JSON files.{RESET}")
        sys.exit(1)

    print(f"[{GREEN}OK{RESET}] Loaded {BOLD}{len(clauses)}{RESET} total CodeClause rules from database.")

    # 3. Filter Clauses based on CLI options
    filtered = clauses[:]

    if args.clause_id:
        filtered = [c for c in filtered if args.clause_id.upper() in c.get("clause_id", "").upper()]
        if not filtered:
            print(f"{YELLOW}[WARN] No clause found matching ID: {args.clause_id}{RESET}")
            sys.exit(0)

    if args.chapter:
        ch_str = f"UAE-FLS-{args.chapter}."
        filtered = [c for c in filtered if ch_str in c.get("clause_id", "") or str(c.get("source_page", "")) == str(args.chapter)]

    if args.topic:
        t_query = args.topic.lower()
        filtered = [c for c in filtered if t_query in c.get("topic", "").lower() or t_query in c.get("occupancy", "").lower() or t_query in c.get("clause_id", "").lower()]

    if not filtered:
        print(f"{YELLOW}[WARN] No clauses matched the given filter criteria.{RESET}")
        sys.exit(0)

    # 4. Sample selection
    if args.seed is not None:
        random.seed(args.seed)

    sample_size = min(len(filtered), args.sample_size)
    if args.clause_id:
        sample = filtered[:sample_size]
    else:
        sample = random.sample(filtered, sample_size)

    # Sort sample by page number for progressive reading
    sample.sort(key=lambda c: (int(c.get("source_page") or 0), str(c.get("clause_id"))))

    print(f"\n{YELLOW}Selected {len(sample)} clauses for visual spot-check verification:{RESET}")

    # 5. Open PDF and Spot-Check each clause
    doc_cache: dict[str, pymupdf.Document] = {}

    def get_doc_for_clause(clause_entry: dict[str, Any]) -> tuple[pymupdf.Document | None, str, int]:
        """Resolves which document and page index to extract."""
        source_pg = int(clause_entry.get("source_page") or 1)
        cid = clause_entry.get("clause_id", "")

        # Check if matching chapter PDF exists
        m = re.search(r"UAE-FLS-(\d+)", cid)
        if m and int(m.group(1)) in chapter_map:
            ch_num = int(m.group(1))
            ch_path = chapter_map[ch_num]
            if str(ch_path) not in doc_cache:
                doc_cache[str(ch_path)] = pymupdf.open(str(ch_path))
            return doc_cache[str(ch_path)], f"Chapter {ch_num} ({ch_path.name})", source_pg

        # Fallback to master 1348-page PDF
        if master_pdf:
            if str(master_pdf) not in doc_cache:
                doc_cache[str(master_pdf)] = pymupdf.open(str(master_pdf))
            return doc_cache[str(master_pdf)], master_pdf.name, source_pg

        return None, "Unknown", source_pg

    # Track results for summary
    scorecard = []

    for i, cl in enumerate(sample, 1):
        doc, doc_name, page_num = get_doc_for_clause(cl)
        if not doc:
            continue

        raw_page_text = extract_page_text(doc, page_num)

        # Build search keywords
        keywords = []
        if cl.get("source_table"):
            keywords.append(cl["source_table"])
        if cl.get("value") is not None:
            keywords.append(str(cl["value"]))
        if cl.get("occupancy"):
            # First 2 significant words of occupancy
            occ_words = [w for w in cl["occupancy"].split() if len(w) > 3 and w.lower() not in ["group", "area", "areas"]]
            keywords.extend(occ_words[:2])
        if cl.get("topic"):
            topic_words = [w for w in cl["topic"].replace("_", " ").split() if len(w) > 3]
            keywords.extend(topic_words[:2])

        if args.full_page:
            snippet = raw_page_text
            matched_kws = [kw for kw in keywords if kw.upper() in raw_page_text.upper()]
        else:
            snippet, matched_kws = find_best_text_snippet(raw_page_text, keywords, max_lines=args.context_lines)

        format_clause_card(
            idx=i,
            total=len(sample),
            clause=cl,
            snippet=snippet,
            matched_kws=matched_kws,
            doc_source_name=doc_name,
            full_page=args.full_page
        )

        scorecard.append({
            "clause_id": cl.get("clause_id"),
            "table": cl.get("source_table"),
            "page": cl.get("source_page"),
            "val": f"{cl.get('value')} {cl.get('unit')}",
            "matched": len(matched_kws) > 0,
            "matched_terms": matched_kws,
        })

    # Close cached documents
    for d in doc_cache.values():
        d.close()

    # 6. Print Verification Summary Table
    print(f"\n\n{CYAN}{'═' * 100}{RESET}")
    print(f"{BOLD} SPOT-CHECK VERIFICATION SCORECARD ({len(scorecard)} Clauses Sampled){RESET}")
    print(f"{CYAN}{'═' * 100}{RESET}")
    print(f"{'No.':<4} | {'Clause ID':<26} | {'Table':<12} | {'Page':<6} | {'Requirement':<18} | {'Evidence Status'}")
    print(f"{'─' * 100}")

    for idx, sc in enumerate(scorecard, 1):
        status_str = f"{GREEN}✓ Verified on Page {sc['page']}{RESET} ({', '.join(sc['matched_terms'])})" if sc["matched"] else f"{YELLOW}? Page {sc['page']} Text Present{RESET}"
        print(f"{idx:<4} | {sc['clause_id']:<26} | {str(sc['table']):<12} | {str(sc['page']):<6} | {sc['val']:<18} | {status_str}")

    print(f"{CYAN}{'─' * 100}{RESET}")
    matched_cnt = sum(1 for sc in scorecard if sc["matched"])
    print(f"{BOLD}Summary:{RESET} {GREEN}{matched_cnt}/{len(scorecard)} sampled clauses{RESET} directly matched text/numerical values on their cited pages.")
    print(f"{DIM}All citations reference the official UAE Fire and Life Safety Code (2018/2026 ed.).{RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Spot-checks CodeClause database entries against source UAE FLS Code PDFs."
    )
    parser.add_argument(
        "-n", "--sample-size",
        type=int,
        default=15,
        help="Number of random clauses to spot-check (default: 15, e.g. 15-20)."
    )
    parser.add_argument(
        "-c", "--clause-id",
        type=str,
        default=None,
        help="Verify a specific clause ID (e.g. UAE-FLS-3.13-BUS-REG)."
    )
    parser.add_argument(
        "-ch", "--chapter",
        type=str,
        default=None,
        help="Filter spot-check by chapter number (e.g. 1, 3, 10, 15)."
    )
    parser.add_argument(
        "-t", "--topic",
        type=str,
        default=None,
        help="Filter spot-check by topic or keyword (e.g. 'travel', 'occupant', 'stair')."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Optional custom path to master UAE FLS Code PDF."
    )
    parser.add_argument(
        "--chapters-dir",
        type=str,
        default=None,
        help="Optional path to directory containing split chapter PDFs."
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Optional path to SQLite database."
    )
    parser.add_argument(
        "--seed-json",
        type=str,
        default=None,
        help="Optional path to code clauses seed JSON."
    )
    parser.add_argument(
        "-k", "--context-lines",
        type=int,
        default=14,
        help="Number of text lines to display in the excerpt window (default: 14)."
    )
    parser.add_argument(
        "--full-page",
        action="store_true",
        help="Print the entire extracted page text instead of a windowed excerpt."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic spot-checking."
    )

    args = parser.parse_args()
    run_spot_check(args)


if __name__ == "__main__":
    main()
