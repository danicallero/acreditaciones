from pathlib import Path
from collections import defaultdict
import csv
import re
import qrcode

# QR settings
ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
ROUNDING = 0.45

# Color mapping
COLORS = {
    'hacker': '#F2F1F2',
    'mentor': '#F2F1F2',
    'organizacion': '#F2F1F2',
    'patrocinador': '#F2F1F2',
}
DEFAULT_COLOR = '#000000'


# --- SVG path construction from matrix ---
def _make_direction_table():
    result = []
    for config in range(16):
        edges = []
        for d in range(4):
            if ((config >> (3 - d)) & 1) == 0 and ((config >> (3 - ((d - 1) % 4))) & 1) != 0:
                edges.append(d)
        result.append(edges)
    return result


DIRECTION_TABLE = _make_direction_table()
DIRECTION_DELTA = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}


def _create_vertices(matrix):
    height = len(matrix)
    width = len(matrix[0]) if height else 0

    def is_dark(col, row):
        return 0 <= col < width and 0 <= row < height and matrix[row][col]

    vertices = []
    for row in range(height + 1):
        for col in range(width + 1):
            config = (
                (1 if is_dark(col, row - 1) else 0)
                | (1 if is_dark(col - 1, row - 1) else 0) << 1
                | (1 if is_dark(col - 1, row) else 0) << 2
                | (1 if is_dark(col, row) else 0) << 3
            )

            edges = DIRECTION_TABLE[config]
            is_corner = len(edges) > 1

            for direction in edges:
                vertices.append((col, row, direction, is_corner))

    return vertices


def _trace_paths(vertices):
    visited = set()
    vertex_lookup = defaultdict(list)

    for i, v in enumerate(vertices):
        vertex_lookup[(v[0], v[1])].append(i)

    def move_by_direction(vertex):
        col, row, direction, _ = vertex
        dx, dy = DIRECTION_DELTA[direction]
        return (col + dx, row + dy)

    def get_next_vertex(current_vertex):
        next_pos = move_by_direction(current_vertex)
        next_indices = vertex_lookup[next_pos]

        if len(next_indices) == 0 or len(next_indices) > 2:
            raise Exception(f"Vertex {next_pos} has invalid connection count: {len(next_indices)}")

        if len(next_indices) == 1:
            return vertices[next_indices[0]]

        v0 = vertices[next_indices[0]]
        v1 = vertices[next_indices[1]]

        if {v0[2], v1[2]} != {(current_vertex[2] - 1) % 4, (current_vertex[2] + 1) % 4}:
            raise Exception(f"Bad next vertex directions: {v0[2]}, {v1[2]} from {current_vertex[2]}")

        ccw_direction = (current_vertex[2] + 1) % 4
        return v1 if v1[2] == ccw_direction else v0

    paths = []
    for start_vertex in reversed(vertices):
        if start_vertex in visited:
            continue

        path = [start_vertex]
        next_vertex = get_next_vertex(start_vertex)

        while next_vertex != start_vertex:
            path.append(next_vertex)
            next_vertex = get_next_vertex(next_vertex)

        paths.append(path)
        visited.update(path)

    return paths


def _render_path_with_smoothing(path, smooth_factor):
    if not path:
        return ""

    def get_smooth_position(vertex, extra_smooth=1.0):
        col, row, direction, _ = vertex
        dx, dy = DIRECTION_DELTA[direction]
        next_col, next_row = col + dx, row + dy

        sc = extra_smooth * smooth_factor / 2.0
        sc1 = 1.0 - sc

        start = (col * sc1 + next_col * sc, row * sc1 + next_row * sc)
        end = (col * sc + next_col * sc1, row * sc + next_row * sc1)
        return start, end

    svg_path = []

    pos_start, _ = get_smooth_position(path[0])
    svg_path.append(f"M{pos_start[0]},{pos_start[1]}")

    for i in range(len(path)):
        current = path[i]
        next_v = path[(i + 1) % len(path)]

        if next_v[2] != current[2]:
            if not next_v[3]:
                ex = 1 - 0.552284749  # circle tweak

                _, bend_start = get_smooth_position(current)
                _, control1 = get_smooth_position(current, ex)
                control2, _ = get_smooth_position(next_v, ex)
                bend_end, _ = get_smooth_position(next_v)

                svg_path.append(f"L{bend_start[0]},{bend_start[1]}")
                svg_path.append(f"C{control1[0]},{control1[1]} {control2[0]},{control2[1]} {bend_end[0]},{bend_end[1]}")
            else:
                svg_path.append(f"L{next_v[0]},{next_v[1]}")

    svg_path.append("Z")
    return " ".join(svg_path)


def render_svg_from_matrix(matrix, fill_color, rounding):
    height = len(matrix)
    width = len(matrix[0]) if height else 0
    empty_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"></svg>'

    if height == 0 or width == 0:
        return empty_svg

    vertices = _create_vertices(matrix)
    if not vertices:
        return empty_svg

    paths = _trace_paths(vertices)
    svg_paths = []
    for path in paths:
        path_d = _render_path_with_smoothing(path, rounding)
        if path_d:
            svg_paths.append(path_d)

    path_data = " ".join(svg_paths)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><path d="{path_data}" fill="{fill_color}"/></svg>'


# --- IO helpers ---
def safe_filename(text):
    text = text.strip()
    text = re.sub(r"[^a-zA-Z0-9-_]+", "_", text)
    return text[:200] if text else "qr"


def make_qr_svg(value, fill_color):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECTION,
        box_size=10,
        border=1,
    )
    qr.add_data(value)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    return render_svg_from_matrix(matrix, fill_color=fill_color, rounding=ROUNDING)


def process_csv(csv_path=Path('salida.csv')):
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {csv_path}")

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader, None)  # skip header if present
        for row in reader:
            if not row or len(row) < 2:
                continue

            t = row[0].strip()
            v = row[1].strip()

            color = COLORS.get(t.lower(), DEFAULT_COLOR)
            svg = make_qr_svg(v, color)

            out_dir = Path('QR') / safe_filename(t)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{safe_filename(v)}.svg"
            out_file.write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    process_csv()