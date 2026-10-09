"""Convert CFF (OTF) fonts to TrueType so Chromium embeds them compactly in PDFs."""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

def otf_to_ttf(src, dst):
    f = TTFont(src)
    gs = f.getGlyphSet(); order = f.getGlyphOrder(); glyf = {}
    for n in order:
        pen = TTGlyphPen(gs); gs[n].draw(Cu2QuPen(pen, 1.0, reverse_direction=True)); glyf[n] = pen.glyph()
    f["loca"] = newTable("loca"); f["glyf"] = g = newTable("glyf"); g.glyphOrder = order; g.glyphs = glyf
    del f["CFF "]
    if "VORG" in f: del f["VORG"]
    f["maxp"] = m = newTable("maxp"); m.tableVersion = 0x00010000
    for a in ("maxZones","maxTwilightPoints","maxStorage","maxFunctionDefs","maxInstructionDefs","maxStackElements","maxSizeOfInstructions","maxComponentElements"):
        setattr(m, a, 0)
    m.maxZones = 1
    f["head"].glyphDataFormat = 0
    f["post"].formatType = 2.0; f["post"].extraNames = []; f["post"].mapping = {}
    f.sfntVersion = "\x00\x01\x00\x00"
    f.save(dst)

if __name__ == "__main__":
    otf_to_ttf(sys.argv[1], sys.argv[2])
