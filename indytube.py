#!/usr/bin/python2.5

#indytube
# Copyright John Duda, 2006
# Copyright Andy Nicholson, 2007 - 2011
# Copyright Anna Helme 2011

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
#3rd party libraries
# templating system
from Cheetah.Template import Template
#twisted networking
from twisted.internet import reactor

class IndyTubeTranscoder(object):

   def __init__(self):
   	"""constructor for IndyTubeTranscoder"""

   def parse_config(self,conf_file):
	"""parse config from the filename argument passed in"""
	config = ConfigParser.RawConfigParser()
	config.read(conf_file)

	self.MENCODER_LOCATION=config.get('mencoder','MENCODER_LOCATION')
	self.MENCODER_OPTIONS=config.get('mencoder','MENCODER_OPTIONS')

	self.FFMPEG_LOCATION=config.get('ffmpeg','FFMPEG_LOCATION')
	self.FFMPEG_IPHONE_OPTIONS=config.get('ffmpeg','FFMPEG_IPHONE_OPTIONS')
	self.FFMPEG_3GP_OPTIONS=config.get('ffmpeg','FFMPEG_3GP_OPTIONS')
        self.FFMPEG_H264_OPTIONS=config.get('ffmpeg','FFMPEG_H264_OPTIONS')

	self.FFMPEG2THEORA_COMMAND=config.get('ffmpeg2theora','FFMPEG2THEORA_COMMAND')
	self.CORTADO_LOCATION=config.get('ffmpeg2theora','CORTADO_LOCATION')

	self.FLVTOOL_LOCATION=config.get('flvtool2','FLVTOOL_LOCATION')

	self.BE_HOW_NICE=config.get('encoder','BE_HOW_NICE') 
	self.CONVERT_THESE=eval(config.get('encoder','CONVERT_THESE'))
	self.DO_ENCODING=config.getboolean('encoder','DO_ENCODING')
	self.NUMBER_OF_PARALLEL_ENCODERS=config.getint('encoder','NUMBER_OF_PARALLEL_ENCODERS')
	self.ENCODER_LOCKFILE_BASE=config.get('encoder','ENCODER_LOCKFILE_BASE')
	self.POLLTIME=int(config.get('encoder','POLLTIME'))

	self.VIDEO_FILE_DIRECTORY=config.get('paths','VIDEO_FILE_DIRECTORY')
	self.FLV_FILE_DIRECTORY=config.get('paths','FLV_FILE_DIRECTORY')
	self.INCLUDE_FILE_DIRECTORY=config.get('paths','INCLUDE_FILE_DIRECTORY')
	self.INCLUDE_FILE_SUFFIX=config.get('paths','INCLUDE_FILE_SUFFIX')
	self.INCLUDE_TEMPLATE=config.get('paths','INCLUDE_TEMPLATE')

	self.FLOWPLAYER_LOCATION=config.get('urls','FLOWPLAYER_LOCATION')
	self.VIDEO_SERVER_URL=config.get('urls','VIDEO_SERVER_URL')
	self.SPLASH_IMAGE_BASE=config.get('urls','SPLASH_IMAGE_BASE')
	self.SPLASH_IMAGE_FILE=config.get('urls','SPLASH_IMAGE_FILE')

	self.LOG_FILE=config.get('logging','LOG_FILE')
	self.LOG_LEVEL=eval(config.get('logging','LOG_LEVEL'))

  	logging.basicConfig(level=self.LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s', filename=self.LOG_FILE, filemode='a') 

	self.ENCODER_LOCKFILE = ""

   def check_lock_file(self):
  	""" inits the logging, and checks for the parallel lock files. If there are no more free spots as an encoder, returns False, else returns True"""
  	self.ENCODER_LOCKFILE=""  #this is dynamic, generated off the base

  	#check we arent already running (up to the number of parallel encoders) and if we are , exit
  	for n in range(0,self.NUMBER_OF_PARALLEL_ENCODERS):
		#set the lockfile name, for later
		self.ENCODER_LOCKFILE="%s.%s" % (self.ENCODER_LOCKFILE_BASE,n)
		if os.path.exists(self.ENCODER_LOCKFILE):	
			if n==(self.NUMBER_OF_PARALLEL_ENCODERS-1):
				logging.error("Max encoders reached(%s), exiting." % self.NUMBER_OF_PARALLEL_ENCODERS)
				#we should exit the program here
				#sys.exit("Max encoders reached(%s), exiting." % self.NUMBER_OF_PARALLEL_ENCODERS)
				return False
		else:
			#we have a free spot , as encoder 'n', lets make the lock file and break out
			os.mknod(self.ENCODER_LOCKFILE)
			break
	return True

   def do_transcoding_loop(self):
	"""do one transcoding loop"""
	logging.info("Starting indytube... in %s " % self.VIDEO_FILE_DIRECTORY)
	checked = 0
	converted = 0
	skipped = 0
	untouched = 0
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

				#check that another encoder isnt already processing this file (lockfile) or that we havent tried and failed before (skipfile) or
				# video file size isnt zero
            			if not(os.path.exists(lockfile) or os.path.exists(skipfile) or os.path.getsize(videofile)<=0):
	        			#OK, valid video file ready to try to transcode
                			logging.debug("Checking file %s, using extension %s " % ( os.path.join(root,f), extension))
                			try:
						try:
                    					os.mknod(lockfile)                # touch the lock file
						except:
							logging.error("lock file creation failed! ABORTING. %s " % lockfile)

							return False

		    				# if the flv or mp4 file (autogenerated) or html snippet is not there, then reencode!
						# lets not worry about the ogg right now
						missing_encoded_file = not(os.path.exists(flvfile)) or not(os.path.exists(mp4file)) or not(os.path.exists(threegpfile)) or not(os.path.exists(newmp4file))
                    				if not(os.path.exists(includefile)) or missing_encoded_file:
							#lets make sure all the directories are created
                                			try:
                                    				os.makedirs(os.path.dirname(flvfile))
                                			except:
                                    				#the dirs may already exist
                                    				pass
							
							#pipe_to_null = '> /dev/null 2>&1'
                        				if self.DO_ENCODING: #maybe we just want to regenerate the include file!
								#mencoder flv conversion
								if not(os.path.exists(flvfile)) or not(os.path.exists(includefile)):
                        						logging.debug('OK to try encoding into FLV: '+videofile)
									start_time=time.time()
									encoder_command = self.MENCODER_LOCATION + " -quiet \"" + videofile + "\" -o \"" + flvfile + "\" " + self.MENCODER_OPTIONS
									os.system('timeout -k 2m 15m nice -n '+self.BE_HOW_NICE+' '+encoder_command)
									finish_time=time.time()
									logging.info("Encoded %s in %.2f seconds, using cmd -- %s" % (videofile,finish_time-start_time,encoder_command))
									flvtool_command = self.FLVTOOL_LOCATION+" -U stdin \""+flvfile + '\"'
									os.system("cat "+ flvfile +" | "+ 'nice -n '+ self.BE_HOW_NICE+' '+flvtool_command) 

			    					#ffmpeg2theora , theora/ogg conversion -- TURNED OFF!!
								if not(os.path.exists(theorafile)) and False:
									logging.debug('OK to try encoding into OGG: '+videofile)
									start_time=time.time()	
									theora_cmd =  self.FFMPEG2THEORA_COMMAND + ' \"' + videofile + "\" -o \"" + theorafile + '\"'
									os.system('timeout -k 2m 15m nice -n '+ self.BE_HOW_NICE+' '+ theora_cmd)
									finish_time=time.time()
									logging.info("Encoded %s in %.2f seconds, using cmd -- %s" % (videofile,finish_time-start_time,theora_cmd))

								#ffmpeg conversion to MP4 for IPhone
								if not(os.path.exists(mp4file)) or not(os.path.exists(includefile)):
									logging.debug('OK to try encoding into MP4: '+videofile)
									start_time=time.time()	
									#ffmpeg_mp4_cmd = self.FFMPEG_LOCATION + ' -i ' + videofile + ' ' + self.FFMPEG_IPHONE_OPTIONS + ' ' + mp4file
									#outputdir is the user's clips directory - ie basedir of mp4file
									output_dir = os.path.dirname(mp4file)
									ffmpeg_mp4_cmd = 'HandBrakeCLI -i \"%s\" -o\"%s\" --optimize --preset="iPhone & iPod Touch"' % (videofile, mp4file)
									os.system('timeout -k 2m 15m nice -n '+ self.BE_HOW_NICE+' '+ ffmpeg_mp4_cmd)
									finish_time=time.time()
									logging.info("Encoded %s in %.2f seconds, using cmd -- %s" % (videofile,finish_time-start_time,ffmpeg_mp4_cmd))

								#ffmpeg conversion to 3GP for other mobiles
								if not(os.path.exists(threegpfile)) or not(os.path.exists(includefile)):
									logging.debug('OK to try encoding into 3GP: '+videofile)	
									start_time=time.time()	
									ffmpeg_3gp_cmd = self.FFMPEG_LOCATION + ' -i \"' + videofile + '\" ' + self.FFMPEG_3GP_OPTIONS + ' \"' + threegpfile + '\"'
									os.system('timeout -k 2m 15m nice -n '+ self.BE_HOW_NICE+' '+ ffmpeg_3gp_cmd)
									finish_time=time.time()
									logging.info("Encoded %s in %.2f seconds, using cmd -- %s" % (videofile,finish_time-start_time,ffmpeg_3gp_cmd))

							        #ffmpeg conversion to new mp4 file ie h264 via ffmpeg
                                                                if not(os.path.exists(newmp4file)) or not(os.path.exists(includefile)):
                                                                        logging.debug('OK to try encoding into new mp4 file: '+videofile)
                                                                        start_time=time.time()
                                                                        ffmpeg_newmp4_cmd = self.FFMPEG_LOCATION + ' -i \"' + videofile + '\" ' + self.FFMPEG_H264_OPTIONS + ' \"' + newmp4file+'.tmp\"'
                                                                        os.system('timeout -k 2m 15m nice -n '+ self.BE_HOW_NICE+' '+ ffmpeg_newmp4_cmd)
									#fast start
									os.system('timeout -k 2m 15m nice -n ' + self.BE_HOW_NICE+ ' qt-faststart \"' + newmp4file + '.tmp\" \"' + newmp4file+'\"')
									os.system("rm \"" + newmp4file + ".tmp\"")
                                                                        finish_time=time.time()
                                                                        logging.info("Encoded %s in %.2f seconds, using cmd -- %s" % (videofile,finish_time-start_time,ffmpeg_newmp4_cmd))

								converted += 1

							else:
								#migration code
								#try to copy old style flv to new style flv file
								if os.path.exists(old_flvfile) and not os.path.exists(flvfile):
									shutil.copyfile(old_flvfile,flvfile)  	

			    					logging.debug("skipped encoding, will just do html template generation, if flv exists as non-zero size")
                    
                    				else:
							logging.debug("transcoded files and html file already exists, not doing transcoding")
							untouched += 1

		    				#make the flash HTML snippet if the flv got created correctly.
		    				#XXX todo, separate out the flv and ogg theora (java applet) html snippet
                    				if os.path.exists(flvfile) and os.path.getsize(flvfile)>0:
                        				logging.debug("Making html template - original size of %s: %.1fMB, Encoded size: %.1fMB" % (videofile,os.path.getsize(videofile)/1000000.0,os.path.getsize(flvfile)/1000000.0))
							#lets make sure all the directories are created
                                			try:
                                    				os.makedirs(os.path.dirname(includefile))
                                			except:
                                    				#the dirs may already exist
                                    				pass

                        				data_map={
									'flowplayer_location':self.FLOWPLAYER_LOCATION, 
									'videofile':relative_directory+'/'+incstem+".flv", 
									'videobaseurl':self.VIDEO_SERVER_URL, 
									'splashbaseurl':self.SPLASH_IMAGE_BASE, 
									'splashfile': relative_directory + '/'+f,
									'cortado_location':self.CORTADO_LOCATION, 
									'oggfile':relative_directory + '/' + incstem+".ogg", 
									'mirid':stem}
                        				t = Template(file=self.INCLUDE_TEMPLATE, searchList=[data_map])  
                        				f=open(includefile, 'w')
                        				f.write(t.respond())
                        				f.close()

                    				else:
                        				logging.info("FLV file size is zero - assuming encoding failed! Permanently skipping file!\n skipfile %s" % skipfile)
                        				os.mknod(skipfile)

						#Another skipfile check for H264 file, which should exist and be larger than 48 bytes.
						if not (os.path.exists(newmp4file) and os.path.getsize(newmp4file)>48):
							logging.info("H264 file missing or < 48 bytes - assuming encoding failed! Permanently skipping file!\n skipfile %s" % skipfile)
                                                        os.mknod(skipfile)


						#
		    				#finished transcoding block , remove lock file 
                    				os.remove(lockfile)

                			except:
                    				logging.error("Error while processing %s: %s" % (videofile,traceback.format_exc()))
						try:
                    					os.remove(lockfile)
						except:
							pass

	   			else:
					logging.debug(' lock file or skip file, or video file size zero : for file %s ' % videofile)
					skipped += 1

	logging.info("Ending indytube... We checked %s eligble files, converted %s files, not transcoded %s files, skipped %s files " % (checked, converted,untouched, skipped))
	## end : do_transcoding_loop


def looperInvoker(indytuber):
    """recursively invoked callback, to check invoking do_transcoding_loop"""
    logging.debug("started looperInvoker function at %s, calling loop every %s seconds " % (time.strftime("%D %H:%M:%S"), indytuber.POLLTIME))
    try:
	#check for others, this creates the ENCODER_LOCKFILE, if we should go ahread and run do_transcoding_loop
	if indytuber.check_lock_file():
		#do transcoding
		indytuber.do_transcoding_loop()
    except:
	logging.error("Error while in looperInvoker: %s" % (traceback.format_exc()))

    #remove this process's lockfile, we have finished the loop
    try:
	os.remove(indytuber.ENCODER_LOCKFILE)
    except:
	pass

    #recursive, time-delayed callback
    #periodically run this function ,to keep looping
    # passing along the indytube object as an argument. (try not to _call_ this function or else you'll end up in infinite recursion!)
    reactor.callLater(indytuber.POLLTIME,looperInvoker,indytuber)

    #END loopInvoker

def main():
    #make an IndyTubeTranscoder object
    indytuber = IndyTubeTranscoder()
    #parse our config
    #find the indytube.conf in the directory that script runs from
    #if not given a path from the system.
    libp = os.path.dirname(sys.argv[0])
    if len(libp) > 0:
        indyconf_path = libp + '/indytube.conf'
    else:
        indyconf_path = './indytube.conf'
    indytuber.parse_config(indyconf_path)
    #we have started!
    logging.info("started main function using conf file %s at %s, calling loop every %s seconds " % (indyconf_path, time.strftime("%D %H:%M:%S"), indytuber.POLLTIME))
    #start it for real, once off
    looperInvoker(indytuber)
    #start the twisted reactor
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
