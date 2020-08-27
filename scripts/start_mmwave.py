import os
import time
import subprocess
import re
import sys

os.system("clear")

start_stamp=time.time()
scripts=os.path.dirname(os.path.realpath(__file__))
waf_dir=scripts+"/../ns3-mmwave-new-handover/"
logs=scripts+"/../mmwave_logs/"


num_ue=1
num_enb=1
simtime=1.0
selected_level=3
log_level=["level_error","level_warn","level_debug","level_info","level_function","level_logic","level_all"]
area_x_size=100
area_y_size=100
area_z_size=100
max_x_velocity=100
max_y_velocity=100
max_z_velocity=0
interval=0.01

if ("-h" in sys.argv) or ("-help" in sys.argv) or ("--help" in sys.argv):
    print "HELP FLAG DETECTED, EXECUTION WILL NOT CONTINUE. RERUN WITHOUT -h, -help AND --help IN ORDER TO CONTINUE THE SIMULATION.\n\n    -ue: The number of User Equipment to include in the simulation.\n    -enb: The number of ENB to include in the simulation.\n    -t: The simulated time to run the simulation.\n    -l: The level of detail to log. The greater the level of detail the longer the simulation will take. Valid options are 0-6 and correspond to the following... %s where * means all available detail. Changing this value can lead to a loss of information and break the parser scripts.\n    -src: The ns3 directory path containing waf executable.\n    -log: The target log file path, pre-existing file of the same name will be removed.\n    -x/-y/-z: The respective length of each dimension. Effectively defining the area to simulate.\n    -xVel/-yVel/-zVel: The maximum acceptable velocity along the respective dimension.\n    -i: The size of the interval to log.\n\n"%(log_level)
    sys.exit()

if "-ue" in sys.argv:
    num_ue=int(sys.argv[sys.argv.index("-ue")+1])

if "-enb" in sys.argv:
    num_enb=int(sys.argv[sys.argv.index("-enb")+1])

if "-t" in sys.argv:
    simtime=float(sys.argv[sys.argv.index("-t")+1])

if "-l" in sys.argv:
    selected_level=int(sys.argv[sys.argv.index("-l")+1])
    if len(log_level)-1<selected_level:
        print "Illegal Logging Level Selected, Exiting"
        sys.exit()

if "-src" in sys.argv:
    waf_dir=str(sys.argv[sys.argv.index("-src")+1])
    if not os.path.isfile(waf_dir+"/waf"):
        print "WAF is not present in provided NS3 directory"
        sys.exit()

if "-log" in sys.argv:
    logs=str(sys.argv[sys.argv.index("-log")+1])

if "-x" in sys.argv:
    area_x_size=int(sys.argv[sys.argv.index("-x")+1])

if "-y" in sys.argv:
    area_y_size=int(sys.argv[sys.argv.index("-y")+1])

if "-z" in sys.argv:
    area_z_size=int(sys.argv[sys.argv.index("-z")+1])

if "-xVel" in sys.argv:
    max_x_velocity=int(sys.argv[sys.argv.index("-xVel")+1])

if "-yVel" in sys.argv:
    max_y_velocity=int(sys.argv[sys.argv.index("-yVel")+1])

if "-zVel" in sys.argv:
    max_z_velocity=int(sys.argv[sys.argv.index("-zVel")+1])
	
if "-i" in sys.argv:
	interval=float(sys.argv[sys.argv.index("-i")+1])

os.system("mkdir -p '"+logs+"'")
target = logs+"/../exec_log.txt"
timelog=waf_dir+"/timelog.txt"

print "Simulation Details: \n    UE:%s; ENB:%s; Time:%s; Log Details: %s\n    NS3 Source: %s\n    Log Location: %s\nLengths(X: %s, Y: %s, Z: %s)\nVelocites(X: %s, Y: %s, Z: %s)\n\n"%(num_ue,num_enb,simtime,log_level[selected_level],waf_dir,target,area_x_size,area_y_size,area_z_size, max_x_velocity, max_y_velocity, max_z_velocity)

if os.path.isfile(target):
    os.system("rm %s"%(target))
    
log_exists=False

if os.path.isfile(timelog):
	os.system("rm "+timelog);

print "Beginning Execution..."
#Runs logging in background so we can track it further down
os.system('''cd %s; ./waf --run="my_sim_modified --simTime=%s --numUe=%s --numEnb=%s --maxX=%s --maxY=%s --maxZ=%s --maxXVel=%s --maxYVel=%s --maxZVel=%s --interval=%s"> %s 2>&1 &'''%(waf_dir, simtime, num_ue,num_enb, area_x_size,area_y_size,area_z_size,max_x_velocity,max_y_velocity,max_z_velocity,interval,target))
print "Execution Called Successfully..."
print "Waiting for Logging",

time.sleep(3)
fail_check=0
while not log_exists:
    if os.path.isfile(target):
        log_exists=True
        sys.stdout.flush()
    else:
        fail_check+=1
        print ".",
        time.sleep(3)
    if fail_check>=10:
        print "\rLog failed to generate within 30 seconds, exiting. Please kill background processes."
        sys.exit()

length=0
running=True
whitespace="     "
waitmsg=" Waiting for Simulation to begin..."
while running:
	if os.path.isfile(timelog):
		tail = " "+subprocess.check_output("tail -n 1 '%s'"%(timelog), shell=True).rstrip("\n\r").lstrip("\n\r")
	else:
		tail=waitmsg
	ps = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE).communicate()[0]
	if "my_sim" not in ps:
		running=False
	else:
		last_line=tail
		sys.stdout.write('\r')
		sys.stdout.flush()
		whitespace = " "*length
		sys.stdout.write("%s\r"%(whitespace))
		sys.stdout.flush()
		sys.stdout.write("%s\r"%(last_line))
		sys.stdout.flush()
		length=len(tail)
	time.sleep(1)

print "\rSimulation Confirmed Complete, Execution Time Approx~ %s\n\n"%((time.time()-start_stamp))
print "Parsing Logs for UE and ENB..."
os.system('''cd %s;python isolate_mmwave.py -ue %s -enb %s -i %s -p %s'''%(scripts,num_ue,num_enb,interval,logs))
os.system('''python parse_cqi.py -p %s -i %s'''%(logs,interval))
os.system('''python clean.py -p %s'''%(logs))
print "Simulation Complete"