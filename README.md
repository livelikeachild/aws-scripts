# aws-scripts
## Intro
This repo provides scripts that can help manage AWS instances. Specifically, if you have a large corpus to process, you can use AWS to create many instances in the same time at your specified price, and process the corpus in parallel. All instances will be automatically stopped once your processing is finished to avoid over-charge.

## Usage

- Write `init.sh` (e.g., [init_script.sh](https://github.com/qiangning/aws-scripts/blob/master/init_script.sh)) and `main.sh` (e.g., [runIllinoisTemporal.sh](https://github.com/qiangning/aws-scripts/blob/master/runIllinoisTemporal.sh))
- `main.sh` must take partition numbers as its first argument; other input arguments should be passed to it via the option `--main_script_args` of `runCluster.py`
- Copy or upload `main.sh` to s3: `s3 cp [path2main.sh] s3://cogcomp-public-data/scripts/main-[uniqueId].sh`, where `uniqueId` is to distinguish different versions of the same script, which you can just type in the date today
- Split the corpus into many partitions (multiply of the number of instances you want to use). For example, if you want to use 100 instances, you can split the large corpus into 100*n partitions. Then you save these partitions to somewhere in s3, say `s3://cogcomp-public-data/results/illinois-temporal/[num].ser.tgz`. This script will evenly distribute all the partitions to each instance.
- Run from the local computer: `python runCluster.py` with arguments. For a full list of arguments, please see the [`run()`](https://github.com/qiangning/aws-scripts/blob/master/runCluster.py#L126-L144) function in `runCluster.py`.
  - `--key_name` is your key name to use AWS.
  - `--private_key_file`` should match to your `key_name` above; this file is typically in `~/.ssh/keyname.pem`.
  - `--count` number of AWS instances you want to use.
  - `--instance_type` type of AWS instance you want to use.
  - `--price` the price you would like to pay for each hour each instance of the type specified above. This price should be slighly higher than the bidding price for that particular type.
  - `--init_script_path` is the init script that runs on all instances before any real processing starts (e.g., create directories and download the program files like .jar files to each instance).
  - `--main_script_path` is the path of main.sh on each instance, which is actually determined by `init.sh`. Remember, in `init.sh`, `main-[uniqueId].sh` is downloaded to each instance (see this [line](https://github.com/qiangning/aws-scripts/blob/master/init_script.sh#L3)).
  - `--input_s3_dir` and `--input_suffix` are where the input files are saved on `s3://cogcomp-public-data/`. For example, in `s3://cogcomp-public-data/results/illinois-temporal/`, there are many `[num].ser.tgz`'s; then `input_s3_dir=results/illinois-temporal/` and `input_suffix=ser.tgz`.
  - `--output_s3_dir` and `--output_suffix` are where the input files are saved on `s3://cogcomp-public-data/`. A special note is that `--output_suffix` can be multiple suffixes split by space, e.g., `arg1 arg2`, which is useful when you want to save multiple types of output. 
