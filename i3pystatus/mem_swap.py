from i3pystatus import IntervalModule
from psutil import swap_memory
from .core.util import round_dict


class Swap(IntervalModule):
    """
    Shows memory load

    .. rubric:: Available formatters

    * {used_swap}

    Requires psutil (from PyPI)
    """

    format = "{used_swap} MiB"
    divisor = 1024 ** 2
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_percentage = 50
    alert_percentage = 80
    round_size = 1

    settings = (
        ("format", "format string used for output."),
        ("divisor",
         "divide all byte values by this value, default is 1024**2 (megabytes)"),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color",
         "defines the color used wann warn percentage ist exceeded"),
        ("alert_color",
         "defines the color used when alert percentage is exceeded"),
        ("round_size", "defines number of digits in round"),

    )

    def run(self):
        swap_usage = swap_memory()
        used = swap_usage.used

        if swap_usage.percent >= self.alert_percentage:
            color = self.alert_color

        elif swap_usage.percent >= self.warn_percentage:
            color = self.warn_color
        else:
            color = self.color

        cdict = {
            "used_swap": used / self.divisor,
        }
        round_dict(cdict, self.round_size)

        if used == 0:
          self.output = {
              "full_text": "",
              }
        else:
          self.output = {
              "full_text": self.format.format(**cdict),
              "color": color
              }
