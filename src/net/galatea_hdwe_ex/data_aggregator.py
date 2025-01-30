#!/usr/bin/python3

# CONFIG = 'config.yaml'
# LOG = 'aggregator.log'
#
# def configModules():
# # get the data by passing a list of modules from the config file
#
#
# # items on the list point to configuration in config file
#     # read the YAML config file (local to this script, nothing fancy yet)
#
#     # configure the modules
#     for module in modules:
#         module_name = module[0]
#         module_id = module
#         module_address = module[1]
#         module_config = module[2]   # this needs to be broken down to constiuent parts
#
#     #return references for each module
# pass
#
# def getData(module):
#     data = None
#
#     # only 1 reading
#         # let the component decide on the representation
#     # do calculation (conversions, calculations, etc) at component
#
#     data = module.getData()
#
#
#     return data
#
# '''
# The standard time.time() function provides sub-second precision, though
# that precision varies by platform. For Linux and Mac precision is +- 1
# microsecond or 0.001 milliseconds. Python on Windows
# uses +- 16 milliseconds precision due to clock implementation problems
# due to process interrupts. The timeit module can provide higher
# resolution if you're measuring execution time.
#
# >>> import time
# >>> time.time()        #return seconds from epoch
# 1261367718.971009
#
# Python 3.7 introduces new functions to the time module that provide
# higher resolution:
#
# >>> import time
# >>> time.time_ns()
# 1530228533161016309
# >>> time.time_ns() / (10 ** 9) # convert to floating-point seconds
# 1530228544.0792289
#
#
# https://realpython.com/python-timer/
#
# time.perf_counter() measures the time in seconds from some unspecified moment in time
# time.monotonic(): timeout and scheduling, not affected by system clock updates
# time.perf_counter(): benchmarking, most precise clock for short period
# time.process_time(): profiling, CPU time of the process (Source)
#
# You can test minimum resolution of time.sleep by doing something like:
#
# from datetime import datetime
# import time
#
# def test_time(delay):
#     start = datetime.now()
#     time.sleep(delay)
#     finish = datetime.now()
#     diff = finish - start
#     return diff.total_seconds()
#
#
#
#
# '''
#
#
# def getElapsedTime():
#     t0 = time.clock()
#     t1 = time.clock() - t0
#     return {t1 - t0:0.4f} # current processor time as a floating point number expressed in seconds.
#
#
#
#
#
#
#
# def makeJSON(moduledata):
#     JSON = None
#
#     # structure the moduledata as JSON
#     # eventID
#     # timestamp
#         #BOX
#             #temp_0 (chan0.value, chan0.voltage)
#             #temp_1 (chan1.value, chan1.voltage)
#             #cpu_temp (temp, other metrics)
#             #x accel
#             #y accel
#             #z accel
#
#         #PUCK
#             #battery
#             #button
#             #time
#             #uptime
#             #temperature
#             #capsense
#             #lux
#             #x accel
#             #y accel
#             #z accel
#             #x gyro
#             #y gyro
#             #z gyro
#
#     return JSON
#
# def makeLOG(moduledata):
#     pass
#
# def makeCSV(moduledata):
#     pass
#
# def aggregate():
#     moduledata = []
#
#     for module in modules:
#         # call getData on the module
#         moduledata.append(getData(module))
#
#     json = makeJSON(moduledata)
#
#     # output JSON   -> structured for consumers
#     file.write(json)
#
#         # output log    -> flat, readable JSON with keys & values
#         logging.debug(flattenJSON(json))
#
#     # output CSV    -> humans and visulizations
#     file.write(jsonToCSV(json))
#
# def startup():
#     # get the logfile location
#     # loadModules & config
#         # loadModules(config)
#     # log the component has started
#     # initialize stats
#     pass
#
# def shutdown():
#     # log the component has started
#     # call disconnections and cleanups
#     pass
#
# def recordData(frame, moduledata):
#     frame_dict.append[frame] = moduledata
#
#
# def writeData(frame):
#
#     makeLOG()
#     makeCVS()
#     makeJSON()
#
#     return True
#
#
#
#
# def main():
#
#     startup()
#
#     #look for the button to be pressed
#
#     # when 'on' (RECORDING)
#         # start the timers
#             # elapsed
#             # puck uptime
#
#         # request incoming data
#         moduledata  = getData(module)
#         # timestamp the data and...
#         # insert the data into the dictionary for the current 'frame'
#         recordData(frame, moduledata)
#         # the dictionary 'frame_dict' needs to expand and contract in memory according to load
#
#
#         # write data from dictionary to disk between frames
#         # apropos conversion method (makeCSV, makeLOG, makeJSON)
#
#         # remove the record from the dictionary after data is written
#     # when "off" (NOT RECORDING)
#         # stop the timers
#         # continue to write data to files
#
#
#
#

if __name__ == '__main__':
    main()

