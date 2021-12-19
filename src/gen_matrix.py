# SPDX-FileCopyrightText: © 2021 Uri Shaked <uri@wokwi.com>
# SPDX-License-Identifier: MIT

from math import log2, ceil

width = 8
height = 8

template = """
// SPDX-FileCopyrightText: © 2021 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

/* DO NOT EDIT - this is an auto-generated file. */
/* generated by gen_matrix.py */

module silife_matrix_{width}x{height} (
    input wire reset,
    input wire clk,
    input wire enable,

    /* Matrix interconnect */
    input wire [{width_minus1}:0] i_n,
    input wire [{height_minus1}:0] i_e,
    input wire [{width_minus1}:0] i_s,
    input wire [{height_minus1}:0] i_w,
    input wire i_ne,
    input wire i_se,
    input wire i_sw,
    input wire i_nw,
    output wire [{width_minus1}:0] o_n,
    output wire [{height_minus1}:0] o_w,
    output wire [{width_minus1}:0] o_s,
    output wire [{height_minus1}:0] o_e,

    /* First port: read/write */
    input  wire [{row_select_bits}:0] row_select,
    input  wire [{width_minus1}:0] clear_cells,
    input  wire [{width_minus1}:0] set_cells,
    output wire [{width_minus1}:0] cells,

    /* Second port: read only */
    input  wire [{row_select_bits}:0] row_select2,
    output wire [{width_minus1}:0] cells2
);

  wire [{offset_bits}:0] row_offset = {{row_select, {col_select_bits}'b0}};
  assign cells = cell_values[row_offset+:{width}];

  wire [{offset_bits}:0] row_offset2 = {{row_select2, {col_select_bits}'b0}};
  assign cells2 = cell_values[row_offset2+:{width}];

  wire [{cell_count}-1:0] cell_values;

  {cells}
endmodule
"""

cell_template = """
  silife_cell cell_{y}_{x} (
      .reset (reset || (row_select == {y} && clear_cells[{x}])),
      .clk   (clk),
      .enable(enable),
      .revive(row_select == {y} && set_cells[{x}]),
      .nw    ({nw}),
      .n     ({n}),
      .ne    ({ne}),
      .e     ({e}),
      .se    ({se}),
      .s     ({s}),
      .sw    ({sw}),
      .w     ({w}),
      .out   (cell_values[{index}])
  );"""


def cell(y, x):
    if y < 0:
        if x < 0:
            return "i_nw"
        if x < width:
            return "i_n[{}]".format(x)
        assert x == width
        return "i_ne"
    if y < height:
        if x < 0:
            return "i_w[{}]".format(y)
        if x < width:
            return "cell_values[{}]".format(y * width + x)
        assert x == width
        return "i_e[{}]".format(y)
    assert y == height
    if x < 0:
        return "i_sw"
    if x < width:
        return "i_s[{}]".format(x)
    assert x == width
    return "i_se"


cells = ""
for y in range(width):
    for x in range(height):
        index = y * width + x
        params = {
            "x": x,
            "y": y,
            "index": index,
            "nw": cell(y - 1, x - 1),
            "n": cell(y - 1, x),
            "ne": cell(y - 1, x + 1),
            "e": cell(y, x + 1),
            "se": cell(y + 1, x + 1),
            "s": cell(y + 1, x),
            "sw": cell(y + 1, x - 1),
            "w": cell(y, x - 1),
        }
        if x == 0:
            cells += "  assign o_w[{}] = cell_values[{}];\n".format(y, index)
        if x == width - 1:
            cells += "  assign o_e[{}] = cell_values[{}];\n".format(y, index)
        if y == 0:
            cells += "  assign o_n[{}] = cell_values[{}];\n".format(x, index)
        if y == height - 1:
            cells += "  assign o_s[{}] = cell_values[{}];\n".format(x, index)
        cells += "  " + cell_template.format(**params).strip() + "\n\n"

width_bits = ceil(log2(width))
height_bits = ceil(log2(height))

print(
    template.format(
        cells=cells[2:],
        width=width,
        width_minus1=width - 1,
        height=height,
        height_minus1=height - 1,
        offset_bits=width_bits + height_bits - 1,
        row_select_bits=height_bits - 1,
        col_select_bits=width_bits,
        cell_count=width * height,
    ).strip()
)
