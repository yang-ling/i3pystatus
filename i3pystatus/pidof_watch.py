#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from subprocess import CalledProcessError
from subprocess import DEVNULL

from i3pystatus import IntervalModule

class PidofWatch(IntervalModule):
  """
  Use pidof command to check whether target process running.
  .. rubric:: Available formatters

  * {name}
  """

  format_up = "{label}"
  format_down = "{label}"
  color_up = "#00FF00"
  color_down = "#FF0000"
  label = ""
  settings = (
    "format_up", "format_down",
    "color_up", "color_down",
    "name", "label",
  )
  required = ("name",)

  def run(self):
    alive = False
    try:
      subprocess.check_call(["pidof", "vsftpd"], stdout=DEVNULL, stderr=DEVNULL)
    except CalledProcessError:
      alive = False
    else:
      alive = True

    if alive:
      fmt = self.format_up
      color = self.color_up
    else:
      fmt = self.format_down
      color = self.color_down

    if self.label == "":
      self.label = self.name

    self.output = {
        "full_text": fmt.format(label=self.label),
        "color": color,
        "instance": self.label
    }
