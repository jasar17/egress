# EGRESS: How Room Function Labels & Physical Geometry Work Together

> **An Explainer on Zero-Trust Architecture:** How EGRESS correctly classifies rooms, applies statutory density factors from the **UAE Fire and Life Safety Code Table 3.13**, and guarantees 100% mathematical precision without relying on unverified drawing numbers.

---

## ❓ 1. The Essential Question & The Critical Distinction

A natural and important question is:
> *"If EGRESS ignores drawing text notes, how does it know whether a room is an office, a meeting room, a cafeteria, or a storage room? If the software just assumes a generic number without reading proper room labels, won't the safety calculations be wrong?"*

To understand why EGRESS is 100% accurate, we must distinguish between **Two Very Different Types of Text on a Blueprint**:

| Drawing Text Category | Examples on Blueprint | How EGRESS Handles It | Why This Is Essential for Safety |
| :--- | :--- | :--- | :--- |
| **1. Room Function Name**<br/>*(Architectural Tag)* | *"MEETING ROOM 1A"*<br/>*"OPEN OFFICE WEST"*<br/>*"SERVER / STORAGE"*<br/>*"PANTRY / BREAKOUT"* | **WE READ & USE THIS.**<br/>The engine reads the room name to identify the statutory occupancy category from UAE Code Table 3.13. | Ensures the correct density factor is selected ($1.4	ext{ m}^2/	ext{p}$ for meeting vs. $9.3	ext{ m}^2/	ext{p}$ for office). |
| **2. Pre-Written Occupant Count**<br/>*(Draftsperson Note)* | *"Occ: 79"*<br/>*"Capacity: 10"*<br/>*"Total: 250 persons"*<br/>*"Max Load: 50"* | **WE REJECT & IGNORE THIS.**<br/>The engine never trusts pre-calculated numbers written on the blueprint. | Prevents human calculation errors, copy-paste drafting mistakes, or deliberate manipulation to bypass safety rules. |

---

## ⚙️ 2. The 4-Tier Room Classification Algorithm

```mermaid
graph TD
    A["Room Polygon Detected from Drawing Vectors"] --> B{"Tier 1: Does room have a recognized text tag?"}
    B -->|Yes (e.g. 'Meeting Room', 'Storage')| C["Apply Table 3.13 Specific Code Factor (1.4, 27.9, etc.)"]
    B -->|No (Unlabeled Space)| D["Tier 2: Apply Project Baseline Factor (e.g. 9.3 m2/p)"]
    C --> E["Calculate Occupant Load = ceil(Geometric Area / Factor)"]
    D --> E
    E --> F["Tier 3: Egress stairs identified as 0 occupant load"]
    F --> G["Tier 4: Reviewer can override classification in UI anytime"]
```

1. **Tier 1 — Semantic Keyword Tag Recognition:** Reads text blocks inside the room polygon and matches keywords (`"MEETING"`, `"PANTRY"` $ightarrow 1.4	ext{ m}^2/	ext{p}$; `"OFFICE"` $ightarrow 9.3	ext{ m}^2/	ext{p}$; `"STORAGE"` $ightarrow 27.9	ext{ m}^2/	ext{p}$; `"RETAIL"` $ightarrow 2.8	ext{ m}^2/	ext{p}$).
2. **Tier 2 — Project Baseline Fallback:** If a room is completely unlabeled, applies the building baseline factor chosen at upload ($9.3	ext{ m}^2/	ext{p}$).
3. **Tier 3 — Spatial Egress Rules:** Stair enclosures and elevator shafts generate 0 occupants.
4. **Tier 4 — Interactive Consultant Override:** Reviewers can click any room on the interactive UI to adjust its classification, updating all paths and rules instantly.

---

## 📊 3. Real-World Proof: Dubai Test Tower Room Calculations

$$	ext{Occupant Load} = \left\lceil rac{	ext{Room Floor Area } (m^2)}{	ext{Code Factor } (m^2/	ext{person})} ightceil$$

| Room Name Tag | Recognized Function | Polygon Area | Table 3.13 Factor | Independent Math Calculation | Final Load |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **OPEN OFFICE WEST** | Regular Office | $65.0	ext{ m}^2$ | $9.3	ext{ m}^2/	ext{p}$ | $65.0 / 9.3 = 6.99 ightarrow \lceil 6.99 ceil$ | **7 persons** |
| **OPEN OFFICE CENTRAL** | Regular Office | $118.0	ext{ m}^2$ | $9.3	ext{ m}^2/	ext{p}$ | $118.0 / 9.3 = 12.69 ightarrow \lceil 12.69 ceil$ | **13 persons** |
| **OPEN OFFICE EAST** | Regular Office | $65.0	ext{ m}^2$ | $9.3	ext{ m}^2/	ext{p}$ | $65.0 / 9.3 = 6.99 ightarrow \lceil 6.99 ceil$ | **7 persons** |
| **MEETING ROOM 1A** | Assembly / Meeting | $37.0	ext{ m}^2$ | $1.4	ext{ m}^2/	ext{p}$ | $37.0 / 1.4 = 26.43 ightarrow \lceil 26.43 ceil$ | **27 persons** |
| **MEETING ROOM 1B** | Assembly / Meeting | $37.0	ext{ m}^2$ | $1.4	ext{ m}^2/	ext{p}$ | $37.0 / 1.4 = 26.43 ightarrow \lceil 26.43 ceil$ | **27 persons** |
| **PANTRY / BREAKOUT** | Assembly / Dining | $37.0	ext{ m}^2$ | $1.4	ext{ m}^2/	ext{p}$ | $37.0 / 1.4 = 26.43 ightarrow \lceil 26.43 ceil$ | **27 persons** |
| **SERVER / STORAGE** | Storage / Utility | $82.0	ext{ m}^2$ | $27.9	ext{ m}^2/	ext{p}$ | $82.0 / 27.9 = 2.94 ightarrow \lceil 2.94 ceil$ | **3 persons** |
| **EXIT STAIR S-01** | Egress Stairwell | $12.5	ext{ m}^2$ | Egress Enclosure | Egress component — 0 load | **0 persons** |

---

## 🎯 4. Summary & Takeaway

* **We DO read room names** to accurately pick the legal density factor ($1.4$, $9.3$, or $27.9	ext{ m}^2/	ext{p}$).
* **We NEVER trust pre-written occupant numbers** (e.g. `"Occ: 79"`), because they are often wrong or copy-pasted.
* **We calculate the true occupant load** by taking the real physical floor area ($m^2$) and dividing by the statutory code factor.
