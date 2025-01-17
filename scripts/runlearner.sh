for seed in 0 1; do
    if [ $2 = exp3a ]
    then
        learnconfig="exp3 --gamma 0.07"
    elif [ $2 = exp3b ]
    then
        learnconfig="exp3 --gamma 0.1"
    elif [ $2 = exp3c ]
    then
        learnconfig="exp3 --gamma 0.25"
    else 
        learnconfig=$2
    fi
    for feature in both probes bow; do
        for reward in binary bump exp; do
            medley ./$1/ ./$1/${2}_${feature}_${reward}_const_${seed}.csv   --classifier $learnconfig --seed $seed --feature_setting $feature --reward $reward --timeout_manager const --set_const 60
            medley ./$1/ ./$1/${2}_${feature}_${reward}_expo_${seed}.csv    --classifier $learnconfig --seed $seed --feature_setting $feature --reward $reward --timeout_manager expo
            medley ./$1/ ./$1/${2}_${feature}_${reward}_nearest_${seed}.csv --classifier $learnconfig --seed $seed --feature_setting $feature --reward $reward --timeout_manager nearest --time_k 20
        done 
    done 
done 