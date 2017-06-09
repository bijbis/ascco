from reportlab.platypus import Flowable


class Line(Flowable):
    """
    Line flowable --- draws a line in a flowable
    """

    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def __repr__(self):
        return "Line(w=%s)" % self.width

    def draw(self):
        """
        draw the line
        """
        self.canv.line(0, self.height, self.width, self.height)
