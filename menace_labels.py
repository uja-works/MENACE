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
    # return unique representations (prevents duplicates for highly symmetric boards)
    uniq = []
    seen = set()
    for bb in boards:
        s = ''.join(bb)
        if s not in seen:
            seen.add(s)
            uniq.append(bb)
    return uniq

def canonical(board: str) -> str:
    """Return the lexicographically smallest symmetry of the board (string)."""
    syms = [''.join(s) for s in all_symmetries(list(board))]
    return min(syms)

def winner(board_str: str):
    """Return 'X' or 'O' if there's a winner, otherwise None."""
    b = board_str
    lines = [
        (0,1,2), (3,4,5), (6,7,8),  # rows
        (0,3,6), (1,4,7), (2,5,8),  # cols
        (0,4,8), (2,4,6)            # diags
    ]
    for i,j,k in lines:
        if b[i] != ' ' and b[i] == b[j] == b[k]:
            return b[i]
    return None

def reachable_positions() -> Set[str]:
    """Traverse the legal game tree from the empty board, stop on wins,
    and collect all reachable boards (all nodes visited)."""
    start = ' ' * 9
    visited = set([start])
    stack = [(start, 'X')]
    while stack:
        board_str, player = stack.pop()
        # Do not expand terminal positions
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
    """Return (canonical -> set(members)), and positions (reachable, X to move, non-terminal)."""
    visited = reachable_positions()
    # positions we care about: X to move (x==o), non-terminal, and at least 2 empty squares
    positions = set()
    for b in visited:
        # only positions where X is to move, no winner, and >1 empty (otherwise no choice)
        if b.count('X') == b.count('O') and winner(b) is None and b.count(' ') > 1:
            positions.add(b)

    canonical_to_members: Dict[str, Set[str]] = collections.defaultdict(set)
    for pos in positions:
        orbit = set(''.join(s) for s in all_symmetries(list(pos)))
        can = min(orbit)
        # store the members (only those that are in positions)
        canonical_to_members[can].add(pos)

    return canonical_to_members, positions

def orbit_stats(canonical_to_members: Dict[str, Set[str]]) -> Dict[int,int]:
    """Return distribution: orbit size -> count of canonical classes with that orbit size.
    Here orbit size = number of distinct members (count of stored members),
    which is <= full orbit size (some symmetric members may be missing due reachability)."""
    dist = collections.Counter()
    for members in canonical_to_members.values():
        dist[len(members)] += 1
    return dict(sorted(dist.items()))

# --- added diagnostics -----------------------------------------------------
def per_depth_stats(canonical_to_members: Dict[str, Set[str]], positions: Set[str]):
    # count how many positions and canonical classes per X-count (0..4)
    pos_by_depth = collections.Counter()
    canon_by_depth = collections.Counter()
    canon_members_by_depth = collections.defaultdict(list)

    for p in positions:
        x = p.count('X')
        pos_by_depth[x] += 1

    for can, members in canonical_to_members.items():
        # pick depth of canonical as depth of any member (all members have same X count)
        any_member = next(iter(members))
        d = any_member.count('X')
        canon_by_depth[d] += 1
        canon_members_by_depth[d].append((can, len(members)))

    print("Per-depth summary (X count = depth):")
    for d in range(0,5):
        print(f" depth {d}: positions={pos_by_depth[d]:4}  canonical_classes={canon_by_depth[d]:4}")

    print("\nExamples of canonical classes per depth (can, members):")
    for d in range(0,5):
        lst = sorted(canon_members_by_depth[d], key=lambda x: (-x[1], x[0]))[:10]
        print(f" depth {d} (show up to 10): {lst}")

if __name__ == "__main__":
    canonical_to_members, positions = build_menace_boxes()
    # Gruppen nach X-Anzahl (0..4) -> vor Zug 1,3,5,7,9
    # statt unsortierter Buckets: erst global sortieren, dann nach Tiefe filtern
    can_to_depth = {can: next(iter(members)).count('X') for can, members in canonical_to_members.items()}
    all_sorted = sorted(canonical_to_members.keys())
    depth_buckets: Dict[int, list] = {d: [can for can in all_sorted if can_to_depth[can] == d] for d in range(0, 5)}

    def grid_lines(label: str) -> list:
        lines = []
        for r in range(3):
            row = label[r*3:(r+1)*3]
            lines.append("     " + " ".join(ch if ch != ' ' else '.' for ch in row))
        return lines

    out_lines = []
    total = 0
    for d in range(0, 5):
        boxes = sorted(depth_buckets[d])
        move_number = 2 * d + 1  # Zug 1,3,5,7,9
        out_lines.append(f"--- Zug {move_number} (X am Zug, X count = {d}) — {len(boxes)} Stellung(en) ---\n")
        for idx, label in enumerate(boxes, 1):
            out_lines.append(f"{idx:3}:")
            out_lines.extend(grid_lines(label))
            out_lines.append("")  # blank line
        total += len(boxes)

    out_lines.append(f"Total canonical boxes: {total}\n")

    with open('/home/uwe/labels.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(out_lines))

    print(f"Wrote labels.txt ({total} boxes)")