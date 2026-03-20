#!/bin/bash
# Auto-typed demo script for asciinema recording

source /Users/lastdance/Desktop/workspace/git_money/llm-medical-guard/.venv/bin/activate

type_cmd() {
    local cmd="$1"
    echo ""
    echo -n "$ "
    for (( i=0; i<${#cmd}; i++ )); do
        echo -n "${cmd:$i:1}"
        sleep 0.03
    done
    echo ""
    sleep 0.3
    eval "$cmd"
    sleep 2
}

clear
echo "  llm-medical-guard v0.2.0 — Demo"
echo "  ================================"
echo ""
sleep 1

# Demo 1: Dangerous content
type_cmd 'llm-medical-guard check -v "Take 50000 IU of vitamin D daily to cure your depression. This miracle supplement has no side effects!"'

sleep 1

# Demo 2: Safe content
type_cmd 'llm-medical-guard check "Vitamin D may support bone health. Typical doses range from 600-1000 IU daily. This is not medical advice - consult your doctor. Source: NIH"'

sleep 1

# Demo 3: Korean
type_cmd 'llm-medical-guard check -l ko "이 약을 먹으면 암 예방이 됩니다! 만병통치약!"'

sleep 1

# Demo 4: Benchmark
type_cmd 'llm-medical-guard bench -n 3000'

sleep 2
echo ""
echo "  pip install llm-medical-guard"
echo "  github.com/MOB-sys/llm-medical-guard"
sleep 3
