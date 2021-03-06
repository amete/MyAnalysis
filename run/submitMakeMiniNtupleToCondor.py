#!/bin/env python
import os
import sys
import glob
import subprocess

ana_type   = "LFV"
use_local = False
susyNtType = "n0235"
userName = "armstro1"
ana_name            = "makeMiniNtuple_LFV"
tar_location        = "/data/uclhc/uci/user/%s/SusyNt/"%(userName)
if use_local:
    filelist_dir        = "/data/uclhc/uci/user/%s/SusyNt/analysis_%s/LOCAL_inputs_LFV/"%(userName,susyNtType)
    in_job_filelist_dir = "/analysis_%s/LOCAL_inputs_LFV/"%(susyNtType)
else:
    filelist_dir        = "/data/uclhc/uci/user/%s/SusyNt/analysis_%s/inputs_LFV/"%(userName,susyNtType)
    in_job_filelist_dir = "/analysis_%s/inputs_LFV/"%(susyNtType)
out_dir             = "/data/uclhc/uci/user/%s/SusyNt/analysis_%s_run/outputs/"%(userName,susyNtType)
log_dir             = "/data/uclhc/uci/user/%s/SusyNt/analysis_%s_run/logs/"%(userName,susyNtType)
samples             = [ "data15",
                        "data16",
                        "Signal",
                        "HWW",
                        "Top",
                        "Diboson",
                        "Zll_ZEW",
                        "Ztt_ZttEW",
                        "Wjets"
                        ]
tarred_dir          = "analysis_%s/"%(susyNtType)
doBrick = True 
doLocal = False 
doSDSC  = False 
doUC    = False 

def main() :
    print "SubmitCondorSF"

    submitMissing=True
    if submitMissing:
        missing_dsids     = []
        missing_dsid_file = open('%s/missing.txt'%(out_dir))
        for dsid in missing_dsid_file:
            missing_dsids.append(dsid.split('\n')[0])
        missing_dsid_file.close()
    look_for_condor_script(brick_ = doBrick, local_ = doLocal, sdsc_ = doSDSC, uc_ = doUC)
    look_for_condor_executable()

    for s in samples :
        if s.startswith('#') : continue
        print "Submitting sample : %s"%s
        suff = ""
        if not s.endswith("/") : suff = "/"
        sample_lists = glob.glob(filelist_dir + s + suff + "*.txt")
        if len(sample_lists) == 0 :
            print "No sample lists in filelist dir!"
            sys.exit()

        for dataset in sample_lists :
            fullname = str(os.path.abspath(dataset))
            print "    > %s"%dataset

            if submitMissing:
                submitDS = False
                for dsid in missing_dsids:
                    if dsid in dataset:
                        submitDS = True
                if not submitDS:
                    continue

            dataset = "." + dataset[dataset.find(in_job_filelist_dir):]
            print "    >> %s"%dataset

            suffix = "-1"
            if "mc15_13TeV" in dataset.split("/")[-1]:
                if "_" in dataset.split("/")[-1].split(".")[3]:
                    suffix = dataset.split("/")[-1].split(".")[3].split("_")[-1]

            if not (str(os.path.abspath(out_dir)) == str(os.environ['PWD'])) :
                print "You must call this script from the output directory where the ntuples will be stored!"
                print " >>> Expected submission directory : %s"%os.path.abspath(out_dir)
                sys.exit()
            
            if s.endswith('DWNLD'): 
                dataset = dataset + '/' 
                print "    >> %s"%dataset        

            run_cmd = "ARGS="
            run_cmd += '"'
            run_cmd += ' %s '%out_dir
            run_cmd += ' %s '%log_dir
            run_cmd += ' %s '%ana_name
            #run_cmd += ' %s '%(tar_location + "area.tgz")
            run_cmd += ' %s '%tarred_dir
            run_cmd += ' %s '%dataset
            if "-1" not in suffix:
                run_cmd += ' -s %s '%(suffix) # any extra cmd line optino for Superflow executable
            run_cmd += '"'
            run_cmd += ' condor_submit submitFile_TEMPLATE.condor '
            lname = dataset.split("/")[-1].replace(".txt", "")
            run_cmd += ' -append "transfer_input_files = %s" '%(tar_location + "area.tgz")
            run_cmd += ' -append "output = %s%s" '%(log_dir, lname + ".out")
            run_cmd += ' -append "log = %s%s" '%(log_dir, lname + ".log")
            run_cmd += ' -append "error = %s%s" '%(log_dir, lname + ".err")

            print run_cmd
            subprocess.call(run_cmd, shell=True)

def look_for_tarball() :
    if not os.path.isfile("area.tgz") :
        print "Tarball not found."
        sys.exit()

def look_for_condor_script(brick_ = False, local_ = False, sdsc_ = False, uc_ = False) :

    brick = 'false'
    local = 'false'
    sdsc  = 'false'
    uc    = 'false'
    if brick_ : brick = 'true'
    if local_ : local = 'true'
    if sdsc_  : sdsc = 'true'
    if uc_    : uc = 'true'

    f = open('submitFile_TEMPLATE.condor', 'w')
    f.write('universe = vanilla\n')
    f.write('+local=%s\n'%brick_)
    f.write('+site_local=%s\n'%local_)
    f.write('+sdsc=%s\n'%sdsc_)
    f.write('+uc=%s\n'%uc_)
    #f.write('transfer_input_files = area.tgz\n')
    f.write('executable = RunCondorSF.sh\n')
    f.write('arguments = $ENV(ARGS)\n')
    f.write('should_transfer_files = YES\n')
    f.write('when_to_transfer_output = ON_EXIT\n')
    #f.write('transfer_output_files = OUTFILE\n')
    #f.write('transfer_output_remaps = OUTFILE_REMAP\n')
    f.write('use_x509userproxy = True\n')
    f.write('notification = Never\n')
    f.write('queue\n')
    f.close()

def look_for_condor_executable() :
    f = open('RunCondorSF.sh', 'w') 
    f.write('#!/bin/bash\n\n\n')
    f.write('echo " ------- RunCondorSF -------- "\n')
    f.write('output_dir=${1}\n')
    f.write('log_dir=${2}\n')
    f.write('sflow_exec=${3}\n')
    f.write('stored_dir=${4}\n')
    f.write('input=${5}\n')
    f.write('sflow_options=${@:6}\n\n')
    f.write('echo "    output directory   : ${output_dir}"\n')
    f.write('echo "    log directory      : ${log_dir}"\n')
    f.write('echo "    sflow executable   : ${sflow_exec}"\n')
    f.write('echo "    tarred dir         : ${stored_dir}"\n')
    f.write('echo "    sample list        : ${input}"\n')
    f.write('echo "    sflow options      : ${sflow_options}"\n\n')
    f.write('while (( "$#" )); do\n')
    f.write('    shift\n')
    f.write('done\n\n')
    f.write('work_dir=${PWD}\n')
    f.write('echo "untarring area.tgz"\n')
    f.write('tar -xzf area.tgz\n\n')
    f.write('echo "done untarring"\n')
    f.write('echo "current directory structure:"\n')
    f.write('ls -ltrh\n\n')
    f.write('export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase\n')
    f.write('source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh\n')
    f.write('echo "Calling : cd ${stored_dir}"\n')
    f.write('cd ${stored_dir}\n')
    f.write('echo "Directory structure:"\n')
    f.write('ls -ltrh\n')
    f.write('lsetup fax\n')
    f.write('source susynt-read/bash/setup_root.sh\n')
    f.write('echo "Calling : source RootCore/local_setup.sh"\n')
    f.write('source RootCore/local_setup.sh\n')
    f.write('echo "Calling : cd MyAnalysis/scripts"\n')
    f.write('cd MyAnalysis/scripts\n')
    f.write('source setRestFrames.sh\n')
    f.write('echo "Calling : cd ${work_dir}"\n')
    f.write('cd ${work_dir}\n')
    f.write('echo "Calling : ${sflow_exec} -f ${input} ${sflow_options}"\n')
    f.write('${sflow_exec} -f ${input} ${sflow_options}\n')
    f.write('echo "final directory structure:"\n')
    f.write('ls -ltrh\n')
    f.close()

if __name__=="__main__" :
    main()

