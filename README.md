# PS2NODE

Converts output of "ps -L -o pid, lwp, psr, comm -p" by assigning corresponding NUMA node for each processor.
        
Read aggregation of CPUs from output of lscpu command.

**Usage**

./ps2node.py --lscpu lscpu.txt < ps.log

or

ps -L -o pid, lwp, psr, comm -p ${PID} | ./ps2node.py --lscpu <(lscpu)
