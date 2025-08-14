import collections
from typing import List, Set, Dict, Tuple

def all_symmetries(board: List[str]) -> List[List[str]]:
    """Generate all 8 symmetries (rotations and reflections) of a 3x3 board."""
    def rotate(b):
        return [b[6], b[3], b[0],
                b[7], b[4], b[1],
                b[8], b[5], b[2]]
    def reflect(b):
        return [b[2], b[1], b[0],
                b[5], b[4], b[3],
                b[8], b[7], b[6]]
    boards = []
    b = board[:]
    for _ in range(4):
        boards.append(b)
        boards.append(reflect(b))
        b = rotate(b)
    # unique
    uniq = []
    seen = set()
    for bb in boards:
        s = ''.join(bb)
        if s not in seen:
            seen.add(s)
            uniq.append(bb)
    return uniq

def canonical(board: str) -> str:
    syms = [''.join(s) for s in all_symmetries(list(board))]
    return min(syms)

def winner(board_str: str):
    b = board_str
    lines = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    for i,j,k in lines:
        if b[i] != ' ' and b[i] == b[j] == b[k]:
            return b[i]
    return None

def reachable_positions() -> Set[str]:
    start = ' ' * 9
    visited = set([start])
    stack = [(start, 'X')]
    while stack:
        board_str, player = stack.pop()
        if winner(board_str) is not None:
            continue
        if ' ' not in board_str:
            continue
        next_player = 'O' if player == 'X' else 'X'
        for i, c in enumerate(board_str):
            if c == ' ':
                b = list(board_str)
                b[i] = player
                nb = ''.join(b)
                if nb not in visited:
                    visited.add(nb)
                    stack.append((nb, next_player))
    return visited

def build_menace_boxes() -> Tuple[Dict[str, Set[str]], Set[str]]:
    visited = reachable_positions()
    positions = set()
    for b in visited:
        if b.count('X') == b.count('O') and winner(b) is None and b.count(' ') > 1:
            positions.add(b)

    canonical_to_members: Dict[str, Set[str]] = collections.defaultdict(set)
    for pos in positions:
        orbit = set(''.join(s) for s in all_symmetries(list(pos)))
        can = min(orbit)
        canonical_to_members[can].add(pos)

    return canonical_to_members, positions

def orbit_stats(canonical_to_members: Dict[str, Set[str]]) -> Dict[int,int]:
    dist = collections.Counter()
    for members in canonical_to_members.values():
        dist[len(members)] += 1
    return dict(sorted(dist.items()))

if __name__ == "__main__":
    canonical_to_members, positions = build_menace_boxes()
    can_to_depth = {can: next(iter(members)).count('X') for can, members in canonical_to_members.items()}
    all_sorted = sorted(canonical_to_members.keys())
    depth_buckets: Dict[int, list] = {d: [can for can in all_sorted if can_to_depth[can] == d] for d in range(0, 5)}

    # write plain text labels
    out_lines = []
    total = 0
    for d in range(0,5):
        boxes = depth_buckets[d]
        move_number = 2 * d + 1
        out_lines.append(f"--- Zug {move_number} (X am Zug, X count = {d}) — {len(boxes)} Stellung(en) ---\n")
        for idx, label in enumerate(boxes, 1):
            out_lines.append(f"{idx:3}:")
            for r in range(3):
                row = label[r*3:(r+1)*3]
                out_lines.append("     " + " ".join(ch if ch != ' ' else '.' for ch in row))
            out_lines.append("")
        total += len(boxes)
    out_lines.append(f"Total canonical boxes: {total}\n")

    with open('labels.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(out_lines))
    print(f"Wrote labels.txt ({total} boxes)")

    # build labels.tex (paged, fits A4 columns)
    tex_path = 'labels.tex'
    cols = 6
    # rows_per_page / per_page will be computed later once box_h_cm is known
    rows_per_page = None
    per_page = None

    color_map = {0:'pastelA',1:'pastelB',2:'pastelC',3:'pastelD',4:'pastelE'}
    color_defs = {
        'pastelA':'FFEBEE','pastelB':'FFF3E0','pastelC':'E8F5E9','pastelD':'E3F2FD','pastelE':'F3E5F5'
    }

    # assemble tex pages
    tex_lines = []
    tex_lines.append(r"\documentclass[10pt]{article}")
    tex_lines.append(r"\usepackage[utf8]{inputenc}")
    tex_lines.append(r"\usepackage{tikz}")
    tex_lines.append(r"\usepackage[margin=10mm,a4paper,landscape]{geometry}")
    tex_lines.append(r"\usepackage{xcolor}")
    tex_lines.append(r"\usetikzlibrary{positioning}")
    tex_lines.append(r"\pagestyle{empty}")
    # remove default inter-column padding (we use explicit p{width} columns)
    tex_lines.append(r"\setlength{\tabcolsep}{0pt}")
    tex_lines.append(r"\begin{document}")
    for name, hexc in color_defs.items():
        tex_lines.append(rf"\definecolor{{{name}}}{{HTML}}{{{hexc}}}")
    # flatten boxes in depth order (grouped by move as requested)
    flattened = []
    for d in range(0,5):
        for can in depth_buckets[d]:
            flattened.append((can,d))
    total_boxes = len(flattened)
    # pages will be computed after we calculate box_h_cm and per_page

    # compute box widths to fit cols on A4 with margin=10mm
    margin_cm = 1.0
    # in landscape mode the usable page width is A4 long side
    paper_w_cm = 29.7
    available_w_cm = paper_w_cm - 2.0 * margin_cm
    gutter_cm = 0.20
    # subtract a small safety margin to account for tabular glue and rounding
    safety_margin = 0.08
    computed_box_w = (available_w_cm - (cols - 1) * gutter_cm) / cols - safety_margin
    computed_box_w = max(2.2, min(computed_box_w, 4.2))

    # --- target physical size for matchbox drawer front (adjust these) ---
    # Matchbox drawer front size (user provided): height 1.5 cm
    target_box_w_cm = 4.8   # width (no change)
    target_box_h_cm = 1.5   # height (cm)  <- set to your measured 1.5 cm
    # ---------------------------------------------------------------------

    # final box width: do not exceed either computed layout width or the physical target
    box_w_cm = min(computed_box_w, target_box_w_cm)
    minipage_w_cm = box_w_cm

    # layout inside box
    index_col = 0.65
    padding = 0.10
    # small right shift of the whole framed box (cm) to move frames slightly to the right
    frame_shift_cm = 0.08

    # compute grid area width available after index column and paddings
    grid_area_w = max(1.8, box_w_cm - index_col - 2.0 * padding)
    # initial cell size based on width
    tikz_cell_from_w = grid_area_w / 3.0
    # initial tikz width/height from width
    tikz_width = 3.0 * tikz_cell_from_w
    tikz_height = tikz_width

    # now check target height constraint and scale down if necessary
    # box inner vertical allowance = target_box_h_cm - vertical padding for captions (0.6 used previously)
    max_grid_height = max(0.0, target_box_h_cm - 0.6)
    # if computed grid height is too large, scale cells to fit the target height
    if tikz_height > max_grid_height and max_grid_height > 0:
        tikz_height = max_grid_height
        tikz_cell_cm = tikz_height / 3.0
        tikz_width = 3.0 * tikz_cell_cm
    else:
        tikz_cell_cm = tikz_cell_from_w

    # reduce caption/padding allowance for very small boxes
    caption_pad = 0.12  # vertical allowance for index area (cm)
    # final box height: respect the target height and ensure a sensible minimum
    box_h_cm = max(1.1, min(target_box_h_cm, tikz_height + caption_pad))

    # extra padding to ensure symbols don't touch/overflow the colored background (smaller for tiny boxes)
    symbol_pad = max(0.04, 0.05 * tikz_cell_cm)  # cm
    # small inset for grid lines so they lie inside the colored background
    line_inset = 0.02  # cm

    # compute how many rows fit on an A4 landscape page to avoid Overfull \vbox
    # A4 short side is 21.0 cm; use same margin_cm as for width
    paper_h_cm = 21.0
    available_h_cm = paper_h_cm - 2.0 * margin_cm
    # vertical gap used in the tabular between rows: "\\[8pt]" -> 8pt in cm
    row_gap_cm = 8.0 * 0.03514598  # 1pt = 0.03514598 cm
    rows_per_page = int((available_h_cm + row_gap_cm) // (box_h_cm + row_gap_cm))
    if rows_per_page < 1:
        rows_per_page = 1
    per_page = cols * rows_per_page
    pages = (total_boxes + per_page - 1) // per_page

    def tikz_for_label(label: str, bgcolor: str, index: int) -> str:
        half_box_w = box_w_cm / 2.0
        # extra horizontal gap (cm) between index and grid
        index_gap_cm = 0.08

        # compute box edges (box is placed at x = frame_shift_cm)
        left_edge = frame_shift_cm - half_box_w
        right_edge = frame_shift_cm + half_box_w

        # compute grid/background sizes
        grid_bg_w = tikz_width + 2*symbol_pad
        grid_bg_h = tikz_height + 2*symbol_pad
        grid_bg_half = grid_bg_w / 2.0

        # desired grid center: just to the right of the index column
        desired_grid_center = left_edge + padding + index_col + index_gap_cm + grid_bg_half

        # clamp grid center so the full colored background stays inside the outer box
        safety = 0.01
        grid_center_x = min(max(desired_grid_center, left_edge + grid_bg_half + safety),
                            right_edge - grid_bg_half - safety)

        # index x: center of the index column, also clamped inside box
        index_x = left_edge + padding + index_col / 2.0
        index_x = min(max(index_x, left_edge + safety), right_edge - safety)

        half_grid_w = tikz_width / 2.0
        half_grid_h = tikz_height / 2.0

        lines = []
        lines.append(r"\begin{tikzpicture}[baseline=(box.base)]")
        # place the outer framed box shifted slightly to the right
        lines.append(rf"  \node[draw,rounded corners=1mm,minimum width={box_w_cm:.2f}cm,minimum height={box_h_cm:.2f}cm,fill=white,inner sep=0pt,outer sep=0pt] at ({frame_shift_cm:.3f}cm,0cm) (box) {{}};")
        # force the tikz bounding box to the box node rectangle (prevents overflow)
        lines.append(r"  \useasboundingbox (box.south west) rectangle (box.north east);")
        # colored background for grid area (add symbol padding so symbols don't touch/overflow)
        lines.append(rf"  \node[draw=none,fill={bgcolor},rounded corners=0.6mm,minimum width={grid_bg_w:.3f}cm,minimum height={grid_bg_h:.3f}cm] at ({grid_center_x:.3f}cm,0cm) {{}};")
        lines.append(r"  \begin{scope}")
        lines.append(r"    \clip (box.south west) rectangle (box.north east);")
        for i in range(1,3):
            y = half_grid_h - i * tikz_cell_cm
            # draw grid lines slightly inset so they remain inside the colored background
            lines.append(rf"    \draw ({grid_center_x - (half_grid_w - line_inset):.3f}cm, {y:.3f}cm) -- ({grid_center_x + (half_grid_w - line_inset):.3f}cm, {y:.3f}cm);")
            x = grid_center_x - half_grid_w + i * tikz_cell_cm
            lines.append(rf"    \draw ({x:.3f}cm, {half_grid_h - line_inset:.3f}cm) -- ({x:.3f}cm, {- (half_grid_h - line_inset):.3f}cm);")
        for r in range(3):
            for c in range(3):
                ch = label[r*3 + c]
                if ch == ' ':
                    continue
                x = grid_center_x - half_grid_w + (c + 0.5) * tikz_cell_cm
                y = half_grid_h - (r + 0.5) * tikz_cell_cm
                # smaller symbol font for matchbox size; zero inner/outer sep
                lines.append(rf"    \node[inner sep=0pt,outer sep=0pt] at ({x:.3f}cm,{y:.3f}cm) {{\scriptsize\textbf{{{ch}}}}};")
        lines.append(r"  \end{scope}")
        # index node: smaller to fit the shallow box
        lines.append(rf"  \node[anchor=center,inner sep=0pt,outer sep=0pt] at ({index_x:.3f}cm, 0cm) {{\small\textbf{{{index}}}}};")
        lines.append(r"\end{tikzpicture}")
        return "\n".join(lines)

    # assemble tex pages
    tex_lines = []
    tex_lines.append(r"\documentclass[10pt]{article}")
    tex_lines.append(r"\usepackage[utf8]{inputenc}")
    tex_lines.append(r"\usepackage{tikz}")
    tex_lines.append(r"\usepackage[margin=10mm,a4paper,landscape]{geometry}")
    tex_lines.append(r"\usepackage{xcolor}")
    tex_lines.append(r"\usetikzlibrary{positioning}")
    tex_lines.append(r"\pagestyle{empty}")
    # remove default inter-column padding (we use explicit p{width} columns)
    tex_lines.append(r"\setlength{\tabcolsep}{0pt}")
    tex_lines.append(r"\begin{document}")
    for name, hexc in color_defs.items():
        tex_lines.append(rf"\definecolor{{{name}}}{{HTML}}{{{hexc}}}")

    for p in range(pages):
        start = p * per_page
        end = min(start + per_page, total_boxes)
        page_items = flattened[start:end]

        tex_lines.append(r"\noindent")
        tex_lines.append(r"\begin{center}")
        # use fixed p{width} columns so total tabular width matches sum of column widths exactly
        col_w = f"{minipage_w_cm:.2f}cm"
        gutter = f"{gutter_cm:.3f}cm"
        # build: @{} p{col_w} @{\hspace{gutter}} p{col_w} ... p{col_w} @{}  (no outer tabcolsep)
        colspec = "@{}" + ("p{" + col_w + "}" + f"@{{\\hspace{{{gutter}}}}}") * (cols - 1) + "p{" + col_w + "}@{}"
        tex_lines.append(r"\begin{tabular}{" + colspec + "}")

        for i, (label, d) in enumerate(page_items):
            overall_index = start + i + 1
            bgcolor = color_map[d]
            tikz = tikz_for_label(label, bgcolor, overall_index)
            # force each table cell to have the same fixed height (prevents vertical overflow)
            cell_h = f"{box_h_cm:.2f}cm"
            # minipage: [c][<height>][c] -> center vertically inside fixed-height box
            cell_tex = r"\begin{minipage}[c][" + cell_h + r"][c]{" + f"{minipage_w_cm:.2f}cm" + "}" + "\n" + tikz + "\n" + r"\end{minipage}"
            tex_lines.append(cell_tex)
            if (i + 1) % cols == 0:
                tex_lines.append(r"\\[8pt]")
            else:
                tex_lines.append("&")
        if len(page_items) % cols != 0:
            tex_lines.append(r"\\")
        tex_lines.append(r"\end{tabular}")
        tex_lines.append(r"\end{center}")
        if p != pages - 1:
            tex_lines.append(r"\clearpage")

    tex_lines.append(r"\end{document}")

    # write tex file
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(tex_lines))
    print(f"Wrote {tex_path} ({total_boxes} boxes, {pages} page(s))")