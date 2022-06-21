# HNL with prompt tau analysis code

## First installation (on lxplus)

- Clone this repositiry
```shell
git clone git@github.com:cms-hnl/HNLTauPrompt.git
```

- Install Luigi Analysis Workflow (for workflow management) if not already installed and setup the environment
```shell
cd HNLTauPrompt/
source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh LCG_101 x86_64-centos7-gcc8-opt
pip install law
source env.sh
```

## Command to run at each login

- Setup the environment
```shell
source env.sh
```

## Law useful commands

- Create an index file (look at tasks dependancies)
```shell
law index --verbose
```

- Print task dependencies 
```shell
law run CreateNanoSkims --version v1 --periods 2018 --print-deps -1
```
- Print status of the task 
```shell
law run CreateNanoSkims --version v1 --periods 2018 --print-status -1
```
- Run task locally (useful for debugging)
```shell
law run CreateNanoSkims --version v1 --periods 2018 --CreateNanoSkims-workflow local
```

- Run task with HTcondor (and the ones required by that task)
```shell
law run CreateNanoSkims --version v1 --periods 2018
```

- If you want to limit the number of jobs running simultaneously (EOS space management)
```shell
law run CreateNanoSkims --version v1 --periods 2018 --CreateNanoSkims-parallel-jobs 100
```

## Helpers to monitor results

- Produce 2 htlm files which contain information on the root file (doc= description of branches, size= exhaustive description of file's size) 
```shell
inspectNanoFile.py -d doc.html -s size.html /eos/user/p/pdebryas/HNL/v1/nanoAOD/2018/HNL_tau_M-1000.root
```