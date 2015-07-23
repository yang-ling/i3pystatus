#!/usr/bin/env python
#
# Copyright (C) 2015 James Murphy
# Licensed under the terms of the GNU GPL v2 only.
#
# i3blocks blocklet script to output connected usb storage device info.

from subprocess import check_output
from i3pystatus import IntervalModule

class Usb(IntervalModule):
  """
  Show removable devices information.
  """

  MOUNTED_COLOR = "green"
  PLUGGED_COLOR = "gray"
  LOCKED_COLOR = "gray"
  UNLOCKED_NOT_MOUNTED_COLOR = "yellow"
  PARTITIONLESS_COLOR = "red"

  # Default texts
  PARTITIONLESS_TEXT = "no partitions"
  SEPARATOR = "<span color='gray'> | </span>"

  # FontAwesome unicode lock/unlock
  FA_LOCK = "\uf023"
  FA_UNLOCK = "\uf09c"

  # Maximum length of a filesystem label to display. Use None to disable
  # truncation, a positive integer to right truncate to that many characters, or
  # a negative integer to left truncate to that many characters. Setting this
  # option to 0 will disable the displaying of filesystem labels.
  TRUNCATE_FS_LABELS = None

  # Edit this function to ignore certain devices (e.g. those that are always
  # plugged in).
  # The dictionary udev_attributes_dict contains all the attributes given by
  # udevadm info --query=propery --name=$path
  def ignore(self, path, udev_attributes_dict):
      # Uncomment to ignore devices whose device name begins with /dev/sda
      if udev_attributes_dict["DEVNAME"].startswith("/dev/sda"):
          return True
      return False

  # Edit this function to ignore devices before the udev attributes are
  # computed in order to save time and memory.
  def fastIgnore(self, path):
      # Uncomment to ignore devices whose path begins with /dev/sda
      if path.startswith("/dev/sda"):
          return True
      return False

  def pangoEscape(self, text):
      return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

  def getLeafDevicePaths(self):
      lines = check_output(['lsblk', '-spndo', 'NAME'], universal_newlines=True)
      lines = lines.split("\n")
      lines = filter(None, lines)
      return lines

  def getKernelName(self, path):
      return check_output(['lsblk', '-ndso', 'KNAME', path],
              universal_newlines=True).rstrip("\n")

  def getDeviceType(self, path):
      return check_output(['lsblk', '-no', 'TYPE', path],
              universal_newlines=True).strip()

  def getFSType(self, path):
      global attributeMaps
      return attributeMaps[path].get("ID_FS_TYPE")

  def isLUKSPartition(self, path):
      return self.getFSType(path) == "crypto_LUKS"

  def getFSLabel(self, path):
      global attributeMaps
      label = attributeMaps[path].get("ID_FS_LABEL_ENC", "")
      if label:
          label = label.encode().decode("unicode-escape")
          if type(self.TRUNCATE_FS_LABELS) == int:
              if self.TRUNCATE_FS_LABELS >= 0:
                  label = label[:self.TRUNCATE_FS_LABELS]
              elif self.TRUNCATE_FS_LABELS < 0:
                  label = label[self.TRUNCATE_FS_LABELS:]
      return label

  def getFSOptions(self, path):
      lines = check_output(['findmnt', '-no', 'FS-OPTIONS', path],
              universal_newlines=True).strip()
      lines = lines.split(",")
      return lines

  def isReadOnly(self, path):
      return "ro" in self.getFSOptions(path)

  def isExtendedPartitionMarker(self, path):
      global attributeMaps
      return attributeMaps[path].get("ID_PART_ENTRY_TYPE") == "0xf"

  def getMountPoint(self, path):
      return check_output(['lsblk', '-ndo', 'MOUNTPOINT', path],
              universal_newlines=True).rstrip("\n")

  def getSpaceAvailable(self, path):
      lines = check_output(['df', '-h', '--output=avail', path],
              universal_newlines=True)
      lines = lines.split("\n")
      if len(lines) != 3:
          return ""
      else:
          return lines[1].strip()

  def getLockedCryptOutput(self, path):
      form = "<span color='{}'>[{} {}]</span>"
      kname = self.getKernelName(path)
      output = form.format(self.LOCKED_COLOR, self.FA_LOCK, kname)
      return output

  def getParentKernelName(self, path):
      lines = check_output(['lsblk', '-nso', 'KNAME', path],
              universal_newlines=True)
      lines = lines.split("\n")
      if len(lines) > 2:
          return lines[1].rstrip("\n")
      else:
          return ""

  def getUnlockedCryptOutput(self, path):
      mountPoint = self.getMountPoint(path)
      if mountPoint:
          color = self.MOUNTED_COLOR
          if self.isReadOnly(path):
              spaceAvail = "ro"
          else:
              spaceAvail = self.getSpaceAvailable(path)
          mountPoint = "<i>{}</i>:".format(self.pangoEscape(mountPoint))
      else:
          color = self.UNLOCKED_NOT_MOUNTED_COLOR
          spaceAvail = ""
      kernelName = self.getKernelName(path)
      parentKernelName = self.getParentKernelName(path)

      block = "<span color='{}'>[{} {}:{}]</span>"
      block = block.format(color, self.FA_UNLOCK, parentKernelName, kernelName)

      label = self.pangoEscape(self.getFSLabel(path))
      if label:
          label = '"{}"'.format(label)

      items = [block, label, mountPoint, spaceAvail]
      return " ".join(filter(None, items))

  def getUnencryptedPartitionOutput(self, path):
      mountPoint = self.getMountPoint(path)
      if mountPoint:
          color = MOUNTED_COLOR
          if self.isReadOnly(path):
              spaceAvail = "ro"
          else:
              spaceAvail = self.getSpaceAvailable(path)
          mountPoint = "<i>{}</i>:".format(self.pangoEscape(mountPoint))
      else:
          color = self.PLUGGED_COLOR
          spaceAvail = ""
      kernelName = self.getKernelName(path)

      block = "<span color='{}'>[{}]</span>"
      block = block.format(color, kernelName)

      label = self.pangoEscape(self.getFSLabel(path))
      if label:
          label = '"{}"'.format(label)

      items = [block, label, mountPoint, spaceAvail]
      return " ".join(filter(None, items))

  def getDiskWithNoPartitionsOutput(self, path):
      form = "<span color='{}'>[{}] {}</span>"
      kernelName = self.getKernelName(path)
      return form.format(self.PARTITIONLESS_COLOR, kernelName, self.PARTITIONLESS_TEXT)

  def getOutput(self, path):
      t = self.getDeviceType(path)
      if t == "part":
          if self.isExtendedPartitionMarker(path):
              return ""
          elif self.isLUKSPartition(path):
              return self.getLockedCryptOutput(path)
          else:
              return self.getUnencryptedPartitionOutput(path)
      elif t == "disk":
          return self.getDiskWithNoPartitionsOutput(path)
      elif t == "crypt":
          return self.getUnlockedCryptOutput(path)
      elif t == "rom" :
          return ""

  def makeAttributeMap(self, path):
      attributeMap = {}
      lines = check_output(
              ['udevadm','info','--query=property','--name={}'.format(path)],
              universal_newlines=True)
      lines = lines.split("\n")
      for line in lines:
          if line:
              key, val = line.split("=", maxsplit=1)
              attributeMap[key] = val
      return attributeMap

  def getAttributeMaps(self, paths):
      return { path : self.makeAttributeMap(path) for path in paths}

  def run(self):
    leaves = self.getLeafDevicePaths()
    leaves = list(filter(lambda path: not self.fastIgnore(path), leaves))
    attributeMaps = self.getAttributeMaps(leaves)
    leaves = filter(lambda path: not self.ignore(path, attributeMaps[path]), leaves)
    outputs = filter(None, map(self.getOutput, leaves))
    output = self.SEPARATOR.join(outputs)
    self.output = {
        "full_text": output,
    }
