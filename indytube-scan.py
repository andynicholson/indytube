#!/usr/bin/python2.6

#indytube-scann
# Copyright Andy Nicholson, 2012

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License,
#  or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
	

import ConfigParser
import os
import logging
import time
import traceback
import sys
import md5 
import shutil
import subprocess
import traceback

#3rd party libraries
#metadata library
import kaa.metadata

class IndyTubeScanner(object):

   def __init__(self):
   	"""constructor for IndyTubeScanner"""

   def parse_config(self,conf_file):
	"""parse config from the filename argument passed in"""
	config = ConfigParser.RawConfigParser()
	config.read(conf_file)

	self.BE_HOW_NICE=config.get('scanner','BE_HOW_NICE') 
	self.CONVERT_THESE=eval(config.get('scanner','CONVERT_THESE'))
	self.DO_SCANNING=config.getboolean('scanner','DO_SCANNING')
	self.SCANNER_LOCKFILE_BASE=config.get('scanner','SCANNER_LOCKFILE_BASE')

	self.VIDEO_FILE_DIRECTORY=config.get('paths','VIDEO_FILE_DIRECTORY')
	self.FLV_FILE_DIRECTORY=config.get('paths','FLV_FILE_DIRECTORY')
	self.INCLUDE_FILE_DIRECTORY=config.get('paths','INCLUDE_FILE_DIRECTORY')
	self.INCLUDE_FILE_SUFFIX=config.get('paths','INCLUDE_FILE_SUFFIX')
	self.INCLUDE_TEMPLATE=config.get('paths','INCLUDE_TEMPLATE')

	self.LOG_FILE=config.get('logging','LOG_FILE')
	self.LOG_LEVEL=eval(config.get('logging','LOG_LEVEL'))

  	logging.basicConfig(level=self.LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s', filename=self.LOG_FILE, filemode='a') 

	self.SCANNER_LOCKFILE = ""

   def check_lock_file(self):
  	""" inits the logging, and checks for the parallel lock files. If there are no more free spots as an encoder, returns False, else returns True"""
  	self.SCANNER_LOCKFILE=""  #this is dynamic, generated off the base

	#set the lockfile name, for later
	n=1
	self.SCANNER_LOCKFILE="%s.%s" % (self.SCANNER_LOCKFILE_BASE,n)
	if os.path.exists(self.SCANNER_LOCKFILE):	
		return False
	else:
		os.mknod(self.SCANNER_LOCKFILE)
		return True

   def shellquote(self,s):
    return "'" + s.replace("'", "'\\''") + "'"


   def do_scanner_loop(self):
	"""do one scanning loop"""
	logging.info("Starting indytube metadata scanner... in %s " % self.VIDEO_FILE_DIRECTORY)
	checked = 0
	same = 0
	different = 0
	error = 0
	for root,dir,files in os.walk(self.VIDEO_FILE_DIRECTORY):
		for f in files:

			#Start the transcoding attempt here, with file 'f'
			#
        		(stem,extension)=os.path.splitext(f)
			#make a unique code from f, and append to f
			# http://plumi.org/ticket/204
			hash=md5.new(f)
			incstem=stem+"-"+hash.hexdigest()
        		if extension.lower() in self.CONVERT_THESE:  #we should convert the file
				checked = checked + 1

            			relative_directory=root[len(self.VIDEO_FILE_DIRECTORY):]
            			if relative_directory.startswith(os.sep):
                			relative_directory=relative_directory[1:]  # make sure we are relative

            			videofile = os.path.join(root,f)
            			lockfile = os.path.join(root,incstem+".wetube_lock")  # we are encoding already
            			skipfile = os.path.join(root,incstem+".wetube_skip")  # we tried and failed, don't bother again
				old_flvfile = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,stem+".flv")
            			flvfile  = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,incstem+".flv")
				#WE NEED TO STRIP '#' out of file names for FLV files
				flvfile = flvfile.replace('#','')
	    			theorafile = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,incstem+".ogg")
				mp4file = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,incstem+".mp4")
				threegpfile = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,incstem+".3gp")
                                newmp4file = os.path.join(self.FLV_FILE_DIRECTORY,relative_directory,incstem+"-h264.mp4")
				newmp4file = newmp4file.replace('#','')

				#use our special 'incstem', which includes our unique hash
            			includefile  = os.path.join(self.INCLUDE_FILE_DIRECTORY,relative_directory,incstem+self.INCLUDE_FILE_SUFFIX)
	    			#logging.info("check for %s, %s, %s " % (lockfile, skipfile, flvfile))

				## Start metadata gathering around file.
				logging.info("Starting analysis on %s " % videofile)
				info = kaa.metadata.parse(videofile)
				if info:
					try:
						video_track_1 = info['video'][0]
						aspect_ratio = float(video_track_1['width']) / float(video_track_1['height'])
						logging.info("Aspect ratio of original is %f for %s" % (aspect_ratio, videofile))
					except:
						logging.warn("Kaa metadata failed on the original file %s\n%s" % (videofile, traceback.format_exc()))
		
						# Try ffprobe and awk
						try:
							aspect_ratio = float(subprocess.Popen(["ffprobe -show_streams "+self.shellquote(videofile)+" 2>&1 | awk -f ffmpeg-results.awk"],stdout=subprocess.PIPE,shell=True).communicate()[0])
							logging.info("According to ffprobe , Aspect ratio of original is %f for %s" % (aspect_ratio, videofile))
						except:
							aspect_ratio = -1
							logging.warn("ffprobe metadata failed on the original file %s\n\%s" % (videofile,traceback.format_exc() ))

				else:
					# Try ffprobe and awk
					try:
						aspect_ratio = float(subprocess.Popen(["ffprobe -show_streams "+self.shellquote(videofile)+" 2>&1 | awk -f ffmpeg-results.awk"],stdout=subprocess.PIPE,shell=True).communicate()[0])
						logging.info("According to ffprobe , Aspect ratio of original is %f for %s" % (aspect_ratio, videofile))
					except:
						aspect_ratio = -1
						logging.warn("ffprobe metadata failed on the original file %s\n\%s" % (videofile,traceback.format_exc() ))


							
				info = kaa.metadata.parse(newmp4file)
				if info:
					try:
						video_track_1 = info['video'][0]
						aspect_ratio_mp4 = float(video_track_1['width']) / (video_track_1['height'])
						logging.info("Aspect ratio of H264 MP4 is %f for %s " % (aspect_ratio_mp4, newmp4file))
					except:
						
						logging.warn("Kaa metadata failed on H264 MP4 file %s\n%s" % (newmp4file,traceback.format_exc()))
						# Try ffprobe and awk
						try:
							aspect_ratio_mp4 = subprocess.Popen(["ffprobe -show_streams "+self.shellquote(newmp4file)+" 2>&1 | awk -f ffmpeg-results.awk"],stdout=subprocess.PIPE).communicate()[0]
							logging.info("According to ffprobe , Aspect ratio of H264 MP4 is %f for %s" % (aspect_ratio_mp4, newmp4file))
						except:
							aspect_ratio_mp4 = -1
							logging.warn("ffprobe metadata failed on H264 MP4 file %s\n%s" % (newmp4file,traceback.format_exc()))


				else:
					# Try ffprobe and awk
					try:
						aspect_ratio_mp4 = subprocess.Popen(["ffprobe -show_streams "+self.shellquote(newmp4file)+" 2>&1 | awk -f ffmpeg-results.awk"],stdout=subprocess.PIPE).communicate()[0]
						logging.info("According to ffprobe , Aspect ratio of H264 MP4 is %f for %s" % (aspect_ratio_mp4, newmp4file))
					except:
						aspect_ratio_mp4 = -1
						logging.warn("ffprobe metadata failed on H264 MP4 file %s\n%s" % (newmp4file,traceback.format_exc()))

				## comparison

				if aspect_ratio_mp4 == -1 or aspect_ratio == -1:	
					error = error + 1
					logging.info('ERROR')
				else:
					#floating point arithmetic
					if abs(aspect_ratio - aspect_ratio_mp4)<0.05:
						same= same + 1
						logging.info(' SAME ! ')
					else:
						different = different + 1
						logging.info('DIFFERENT')
						
						#lets get rid of the MP4 file - it will be re-encoded hopefully at the right resolution.
						os.remove(newmp4file)
					

	logging.info("Ending indytube scanning... We checked %s eligble files, same %s files, different %s files, error %s files " % (checked, same, different, error))
	## end : do_scanner_loop


def looperInvoker(indytuber):
    """recursively invoked callback, to check invoking do_scanner_loop"""
    logging.debug("started looperInvoker function at %s " % (time.strftime("%D %H:%M:%S")))
    try:
	#check for others, this creates the SCANNER_LOCKFILE, if we should go ahread and run do_scanner_loop
	if indytuber.check_lock_file():
		#do transcoding
		indytuber.do_scanner_loop()
    except:
	logging.error("Error while in looperInvoker: %s" % (traceback.format_exc()))

    #remove this process's lockfile, we have finished the loop
    try:
	os.remove(indytuber.SCANNER_LOCKFILE)
    except:
	pass

    #END loopInvoker

def main():
    #make an IndyTubeScanner object
    indytuber = IndyTubeScanner()
    #parse our config
    #find the indytube.conf in the directory that script runs from
    #if not given a path from the system.
    libp = os.path.dirname(sys.argv[0])
    if len(libp) > 0:
        indyconf_path = libp + '/indytube-scan.conf'
    else:
        indyconf_path = './indytube-scan.conf'
    indytuber.parse_config(indyconf_path)
    #we have started!
    logging.info("started main function using conf file %s at %s " % (indyconf_path, time.strftime("%D %H:%M:%S")))
    #start it for real, once off
    if indytuber.DO_SCANNING:
	    looperInvoker(indytuber)
    

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
