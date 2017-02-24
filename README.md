# PS2NODE

Converts output of "ps -L -o pid, lwp, psr, comm -p" by assigning corresponding NUMA node for each processor.
        
Read aggregation of CPUs from output of lscpu command.

**Usage**

        ./ps2node.py --lscpu lscpu.txt < ps.log

        or

        ps -L -o pid, lwp, psr, comm -p ${PID} | ./ps2node.py --lscpu <(lscpu)


**To process many files and replace original files:**

        for file in $(find ./ -name "*ps.log") ; do

                temp_file=$(mktemp)
  
                ./ps2node.py --lscpu lscpu.txt <"${file}" >"${temp}"
  
                if [[ $? == 0 ]] && [[ -s "${temp_file}" ]] ; then
  
                        mv "${temp_file}" "${file}"
    
                else
  
                        echo "ps2node.py has failed for file \"${file}\"" 1>&2
    
                        rm "${temp_file}"
    
                fi  
  
        done
