#-------------------------------------------------------------------------------
import re
import math
#-------------------------------------------------------------------------------
class SimpleFont:
    def __init__(self, data):
        self.glyphs = {}
        self.load_glyphs(data)
#-------------------------------------------------------------------------------
    # Load more glyphs from data (as if generated by scripts/genfont.pl).
    # Supersedes previous glyphs on clash.
    def load_glyphs(self, data):
        lines = [x.strip() for x in data]
        mode = "need_header"
        write_to = None
        bitmap = None
        m = None
        for line in lines:
            p = re.compile('(\d+) (\d+) (\d+)')
            regex_tuple = p.findall(line)
            if mode == "need_header" and regex_tuple:
                bitmap = []
                m = regex_tuple[0] 
                write_to = {"shift_h" : m[1] , "shift_v" : m[2]}
                self.glyphs[m[0]] = write_to
                mode = "need_line"
            elif mode == "need_line":
                if not line:
                    mode = "need_header"
                    write_to["bitmap"] = bitmap
                    self.glyphs[m[0]] = write_to
                else:
                    bitmap += line.split('\n')
#-------------------------------------------------------------------------------
    # Render string given the max height above the baseline. Returns rectangular
    # array, starting from top-left corner.
    # Opts: 
    #  ignore_shift_h - whether to ignore shift_h read from the font.
    #  fixed_width - make width exactly this, cropping or pannin the text to it.
    def render(self, string, height, opts = {}):

        # We'll store, temporarily, bits in buf hash where hash[[i,j]] is a bit.
        # i points up, and j points right from the start of the baseline. 
        buf = {}
        width = 0

        for x in string:
            c_code = str(ord(x))
            glyph = self.glyphs[c_code]
            add_shift_h = None
            if "ignore_shift_h" in opts:
                if opts["ignore_shift_h"]:
                    add_shift_h = 0
            else:
                add_shift_h = glyph["shift_h"]
            for i, row in enumerate(glyph["bitmap"]):
                for j, bit in enumerate(row):
                    bit_row = (int(glyph["shift_v"]) - 1) - i
                    bit_col = width + j + add_shift_h
                    buf[(bit_row, bit_col)] = bit
                    if bit_row < 0:
                        print "negative value for letter %s" % c_code
            # Compute the new width.
            if glyph["bitmap"][0]:
                width += len(glyph["bitmap"][0]) 
            else:
                width += 0
            # Insert interval between letters.
            width += 1 + add_shift_h

        # Return error if pic is bigger than allowed for
        if width > opts["fixed_width"]:
            return None

        # now render the final array
        result = [[0] * opts['fixed_width'] for i in xrange(height)]

        for xy in buf:
            bit = buf[xy]
            row = (height - 1) - xy[0]
            col = xy[1]
            result[row][col] = bit

        # Update width from mere maximum width to preset width if any.
        text_width = width
        image_width = None
        if opts["fixed_width"]:
            image_width = opts["fixed_width"]
        else:
            image_width = width

        # Center the row
        for i, row in enumerate(result):
            # Check how much we should *remove* from right
            slice_total = text_width - image_width

            # How much to slice from the right & put back in the left
            slice_l = int(math.floor(slice_total/2))

            # Slice right & pad left
            if slice_total < 0:
                sliced_row = row[:slice_l]
                expanded_row = [0] * int(math.fabs(slice_l)) + sliced_row
                result[i] = expanded_row

        return result
#-------------------------------------------------------------------------------
    # Same as render, but renders several lines (its an array), and places them
    # below each other.  Accepts the same options as "render," and also these:
    # distance: distance between lines in pixels.
    def render_multiline(self, lines, line_height, opts = {}):
        line_pics = [self.render(line, line_height, opts) for line in lines]
        canvas = []
        for line in line_pics:
            if not line:
                return None
            canvas += line
        return canvas
#-------------------------------------------------------------------------------
# Returns the default, most useful instance of the font used in signs.
def sign_font(glyphs_path):
    sf = SimpleFont(\
            open('/'.join([glyphs_path,'7x7.simpleglyphs'])).readlines())

    # Load amendments to the letters I don't like.
    sf.load_glyphs(\
            open('/'.join([glyphs_path,'amends.simpleglyphs'])).readlines())

    # Load local, application-specific glyphs.
    sf.load_glyphs(\
            open('/'.join([glyphs_path,'specific.simpleglyphs'])).readlines())

    return sf
#-------------------------------------------------------------------------------
