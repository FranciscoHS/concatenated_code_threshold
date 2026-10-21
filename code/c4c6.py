import stim
import random
import numpy as np
import json
import sys

def append_noisy_wait(circuit,list_loc,N,p,steps=1):
    ew =  3/4*(1-(1-4/3*gamma)**steps)
    for i in list_loc:
        for j in range(N):
            circuit.append("DEPOLARIZE1", i+j, ew)

def reset(circuit,loc,N):
    for i in range(N):
        circuit.append("M", loc+i)
    for i in range(N):
        circuit.append("CNOT", [stim.target_rec(i-N), loc+i])
        
def noisy_reset(circuit,loc,N,p):
    for i in range(N):
        circuit.append("M", loc+i)
    for i in range(N):
        circuit.append("CNOT", [stim.target_rec(i-N), loc+i])
    for i in range(N):
        circuit.append("X_ERROR", loc+i, p)

def append_h(circuit, loc, N_prev, N_now):
    if N_prev==1:
        for i in range(N_now):
            circuit.append("H", loc+i)
        if N_now==4:
            circuit.append("SWAP", [loc+1, loc+2])
    else:
        for i in range(N_now):
            append_h(circuit, (loc+i)*N_prev, 1, N_prev)
        if N_now==3:
            for i in range(3):
                circuit.append("SWAP", [(loc+i)*N_prev+1, (loc+i)*N_prev+3])
                circuit.append("SWAP", [(loc+i)*N_prev+1, (loc+i)*N_prev+2])
def append_transversal_h(circuit, loc, N_prev, N_now):
    if N_prev==1:
        for i in range(N_now):
            circuit.append("H", loc+i)
    else:
        for i in range(N_now):
            append_h(circuit, (loc+i)*N_prev, 1, N_prev)
            
def append_swap(circuit, loc1, loc2, N_prev, N_now):
    for i in range(N_prev*N_now):
        circuit.append("SWAP", [N_prev*loc1+i, N_prev*loc2+i])

    
def append_cnot(circuit, loc1, loc2, N_prev, N_now):
    N=N_prev*N_now
    for i in range(N):
        circuit.append("CNOT", [loc1*N_prev+i, loc2*N_prev+i])
        
def append_noisy_cnot(circuit, loc1, loc2, N_prev, N_now, p):
    N=N_prev*N_now
    for i in range(N):
        circuit.append("CNOT", [loc1*N_prev+i, loc2*N_prev+i])
    for i in range(N):
        circuit.append("DEPOLARIZE2", [loc1*N_prev+i,loc2*N_prev+i], p)

def append_m(circuit, loc, N_prev, N_now):
    global detector_now
    
    if N_prev==1:
        for i in range(N_now):
            circuit.append("M", loc+i)
        for i in range(N_now):
            circuit.append("DETECTOR",stim.target_rec(i-N_now))
        detector_m=[detector_now, detector_now+N_now]
        detector_now+=N_now
    else:
        detector_m=[append_m(circuit, (loc+i)*N_prev, 1, N_prev) for i in range(N_now)]
    
    return detector_m

def append_noisy_m(circuit, loc,N_prev,N_now, p):
    global detector_now
    
    if N_prev==1:
        for i in range(N_now):
            circuit.append("X_ERROR", loc+i, p)
        for i in range(N_now):
            circuit.append("M", loc+i)
        for i in range(N_now):
            circuit.append("DETECTOR",stim.target_rec(i-N_now))
        detector_m=[detector_now, detector_now+N_now]
        detector_now+=N_now
    else:
        detector_m=[append_noisy_m(circuit, (loc+i)*N_prev, 1, N_prev, p) for i in range(N_now)]
    
    return detector_m
        
def append_0prep(circuit, loc1, N_prev, N_now):
    if N_prev==1:
        reset(circuit,loc1,N_now)
    else:
        for i in range(N_now):
            append_0prep(circuit, (loc1+i)*N_prev, 1, N_prev)

    if N_now==N_c4:
        append_h(circuit,(loc1+0)*N_prev,1,N_prev)
        append_cnot(circuit, (loc1+0)*N_prev, (loc1+1)*N_prev,1,N_prev)
        append_cnot(circuit, (loc1+0)*N_prev, (loc1+2)*N_prev,1,N_prev)
        append_cnot(circuit, (loc1+0)*N_prev, (loc1+3)*N_prev,1,N_prev)

def append_noisy_0prep(circuit, loc1, loc2, N_prev, N_now, p):
    global detector_now
    
    if N_now==N_c6:
        n_now=3
    else:
        n_now=N_now
    
    if N_prev==1:
        noisy_reset(circuit,loc1,N_now,p)
        noisy_reset(circuit,loc2,N_now,p)
        detector_0prep = []
    else:
        detector_0prep = []
        for i in range(n_now):
            detector_0prep.append(append_noisy_0prep(circuit, (loc1+i)*N_prev, (loc1+n_now+i)*N_prev, 1, N_prev, p))
        for i in range(n_now):
            detector_0prep.append(append_noisy_0prep(circuit, (loc2+i)*N_prev, (loc2+n_now+i)*N_prev, 1, N_prev, p))
    if N_now==N_c4:
        for i in range(4):
            circuit.append("H", loc2+i)
        
        for i in range(N_now):
            append_noisy_cnot(circuit, (loc2+i)*N_prev, (loc1+i)*N_prev, 1, N_prev, p)
        
        for i in range(N_now):
            append_noisy_cnot(circuit, (loc1+i)*N_prev, (loc2+(i+1)%N_now)*N_prev, 1, N_prev, p)

        detector_0prep.append(append_noisy_m(circuit,loc2,N_prev,N_now,p))
        for i in range(N_now-1):
            for j in range(N_now-1):
                if j>=i:
                    append_cnot(circuit, (loc2+i)*N_prev, (loc1+j)*N_prev,1,N_prev)

        return detector_0prep
    elif N_now==N_c6:
        for i in range(3):
            append_h(circuit,(loc2+i)*N_prev,1,N_c4)
            append_noisy_cnot(circuit,(loc2+i)*N_prev,(loc1+i)*N_prev,1,N_c4,p)
        for i in range(3):
            append_noisy_cnot(circuit,(loc1+i)*N_prev,(loc2+((i+1)%3))*N_prev,1,N_c4,p)
        detector_0prep.append(append_noisy_m(circuit,loc2,N_prev,3,p))
        
        append_cnot(circuit,(loc2+0)*N_prev, (loc1+0)*N_prev,1,N_prev)
        append_cnot(circuit,(loc2+0)*N_prev, (loc1+1)*N_prev,1,N_prev)
        append_cnot(circuit,(loc2+1)*N_prev, (loc1+1)*N_prev,1,N_prev)
        
        circuit.append("SWAP", [(loc1+1)*N_c4+1, (loc1+1)*N_c4+2])
        circuit.append("SWAP", [(loc1+1)*N_c4+1, (loc1+1)*N_c4+3])
        
        circuit.append("SWAP", [(loc1+2)*N_c4+1, (loc1+2)*N_c4+3])
        circuit.append("SWAP", [(loc1+2)*N_c4+1, (loc1+2)*N_c4+2])
        
        return detector_0prep

def decode_measurement_c4(m, m_type='x'):
    #Hard-decision decoder for c4
    if (int(m[0])+int(m[1])+int(m[2])+int(m[3]))%2==1:
        outcome=[-1,-1]
    else:
        outcome=[(int(m[0])+int(m[2]))%2,(int(m[2])+int(m[3]))%2]
    
    return outcome

def decode_measurement_c6(m, m_type='x'):
    if len(m)==3:
        M=[m[0][0],m[0][1],m[1][0],m[1][1],m[2][0],m[2][1]]
    else:
        M=m
    if [M[0],M[2],M[4]].count(-1)>1:
        outcome=[-1,-1]
    elif M[0]==-1:
        outcome=[(M[2]+M[3]+M[5])%2, (M[3]+M[4])%2]
    elif M[2]==-1:
        outcome=[(M[1]+M[4]+M[5])%2, (M[0]+M[5])%2]
    elif M[4]==-1:
        outcome=[(M[0]+M[1]+M[3])%2, (M[1]+M[2])%2]
    else:
        if (M[0]+M[1]+M[2]+M[5])%2==1 or (M[0]+M[3]+M[4]+M[5])%2==1:
            outcome=[-1,-1]
        else:
            outcome=[(M[2]+M[3]+M[5])%2, (M[3]+M[4])%2]
    return outcome

def append_noisy_ec(circuit, loc1, loc2, loc3, loc4, N_prev, N_now, p, no_verification=-1):
    global detector_now, no_ec
    detector_0prep = []
    detector_Z=[]
    detector_X=[]
    
    if N_now==1:
        return None
    
    if N_now==N_c6:
        n_now=3
    else:
        n_now=N_now

    detector_0prep.extend(append_noisy_0prep(circuit, loc2, loc4, N_prev, N_now, p))
    detector_0prep.extend(append_noisy_0prep(circuit, loc3, loc4, N_prev, N_now, p))
    append_h(circuit,loc2,N_prev,n_now)
    append_noisy_cnot(circuit,loc2,loc3,N_prev,n_now, p)
    
    if N_now==N_c6 and no_ec==False:#Error detecting teleportation
        for i in range(3):
            detector_0prep_c4, detector_Z_c4, detector_X_c4 = append_noisy_ec(circuit,(loc2+i)*N_prev,(loc4+0)*N_prev,(loc4+1)*N_prev,(loc4+2)*N_prev,1,N_prev,p)
            append_h(circuit,(loc2+i)*N_prev,1,N_prev)
            append_cnot(circuit,(loc4+1)*N_prev,(loc2+i)*N_prev,1,N_prev)
            append_h(circuit,(loc2+i)*N_prev,1,N_prev)
            append_cnot(circuit,(loc4+0)*N_prev,(loc2+i)*N_prev,1,N_prev)
            detector_0prep.extend(detector_0prep_c4)
            detector_Z.append(detector_Z_c4)
            detector_X.append(detector_X_c4)
        for i in range(3):
            detector_0prep_c4, detector_Z_c4, detector_X_c4 = append_noisy_ec(circuit,(loc3+i)*N_prev,(loc4+0)*N_prev,(loc4+1)*N_prev,(loc4+2)*N_prev,1,N_prev,p)
            append_h(circuit,(loc3+i)*N_prev,1,N_prev)
            append_cnot(circuit,(loc4+1)*N_prev,(loc3+i)*N_prev,1,N_prev)
            append_h(circuit,(loc3+i)*N_prev,1,N_prev)
            append_cnot(circuit,(loc4+0)*N_prev,(loc3+i)*N_prev,1,N_prev)
            detector_0prep.extend(detector_0prep_c4)
            detector_Z.append(detector_Z_c4)
            detector_X.append(detector_X_c4)
    
    append_noisy_cnot(circuit,loc1,loc2,N_prev,n_now, p)
    
    append_h(circuit,loc1,N_prev,n_now)
    
    detector_Z.append(append_noisy_m(circuit,loc1,N_prev,n_now, p))
    detector_X.append(append_noisy_m(circuit,loc2,N_prev,n_now, p))
    
    append_swap(circuit,loc1,loc3,N_prev,n_now)
    
    return detector_0prep, detector_Z, detector_X

def decode_ec_hd(x, detector_X, detector_Z):
    mx=[[]]*3
    mz=[[]]*3
    
    for i in range(3):
        detx=detector_X[i]
        detz=detector_Z[i]
        mx[i]=decode_measurement_c4(x[detx[0]:detx[1]], 'x')
        mz[i]=decode_measurement_c4(x[detz[0]:detz[1]], 'z')
    
    correction_x = decode_measurement_c6(mx, 'x')
    correction_z = decode_measurement_c6(mz, 'z')
    
    return correction_x, correction_z

def decode_m_hd(x, detector_m):
    m=[[]]*3
    for i in range(3):
        det=detector_m[i]
        m[i]=decode_measurement_c4(x[det[0]:det[1]])
    
    outcome = decode_measurement_c6(m, 'x')
    
    return outcome

def post_selection_c4(x,detector_0prep):
    if sum(x[detector_0prep[0]:detector_0prep[1]])%2==0:
        return True
    else:
        return False

def post_selection_c6(x,detector_0prep):
    outcome=[[]]*3
    for i in range(3):
        outcome[i]=decode_measurement_c4(x[detector_0prep[i][0]:detector_0prep[i][1]])
        if outcome[i][0]==-1:
            return False
    if (outcome[0][0]+outcome[1][0]+outcome[2][0])%2==0 and (outcome[0][1]+outcome[1][1]+outcome[2][1])%2==0:
        return True
    else:
        return False

def accept(x,list_detector_m,list_detector_X,list_detector_Z,Q=1):
    global no_ec
    num_correction=2*Q

    X_propagate=[[1],[3]]
    Z_propagate=[[0],[2]]
    outcome = np.zeros([4,2])
    correction_x = np.zeros([num_correction,2])
    correction_z = np.zeros([num_correction,2])
    
    # Post selection at error detecting telportation
    if no_ec==False:
        for i in range(num_correction):
            for a in range(6):
                if decode_measurement_c4(x[list_detector_X[i][a][0][0]:list_detector_X[i][a][0][1]])[0]==-1:
                    return -1
                if decode_measurement_c4(x[list_detector_Z[i][a][0][0]:list_detector_Z[i][a][0][1]])[0]==-1:
                    return -1
    
    for i in range(num_correction):
        if no_ec==False:
            correction_x[i,:], correction_z[i,:] = decode_ec_hd(x, list_detector_X[i][6], list_detector_Z[i][6])
        else:
            correction_x[i,:], correction_z[i,:] = decode_ec_hd(x, list_detector_X[i][0], list_detector_Z[i][0])
    
    for i in range(4):
        outcome[i,:] = decode_m_hd(x, list_detector_m[i])

    for a in range(2):
        for i in range(num_correction):
            pos = i%2
            for x_prop in X_propagate[pos]:
                if outcome[x_prop,a]==-1:
                    continue
                if correction_x[i,a]==1:
                    outcome[x_prop,a] = (outcome[x_prop,a]+1)%2
                if correction_x[i,a]==-1:
                    outcome[x_prop,a] = -1
            for z_prop in Z_propagate[pos]:
                if outcome[z_prop,a]==-1:
                    continue
                if correction_z[i,a]==1:
                    outcome[z_prop,a] = (outcome[z_prop,a]+1)%2
                if correction_z[i,a]==-1:
                    outcome[z_prop,a] = -1
    
    num_errors = 0
    for a in range(2):
        flag=1
        for i in range(4):
            if outcome[i,0]==1:
                flag=0
            if outcome[i,0]==-1:
                flag*=0.5
        num_errors += (1-flag)
    return num_errors

def accept_c4(x,list_detector_m,list_detector_X,list_detector_Z,Q=1):
    num_correction=2*Q

    X_propagate=[[1],[3]]
    Z_propagate=[[0],[2]]
    outcome = np.zeros([4,2])
    correction_x = np.zeros([num_correction,2])
    correction_z = np.zeros([num_correction,2])
    
    for i in range(4):
        outcome[i,:] = decode_measurement_c4(x[list_detector_m[i][0]:list_detector_m[i][1]], 'x')

    for i in range(num_correction):
        correction_x[i,:] = decode_measurement_c4(x[list_detector_X[i][0][0]:list_detector_X[i][0][1]], 'x')
        correction_z[i,:] = decode_measurement_c4(x[list_detector_Z[i][0][0]:list_detector_Z[i][0][1]], 'z')


    for a in range(2):
        for i in range(num_correction):
            pos = i%2
            for x_prop in X_propagate[pos]:
                if outcome[x_prop,a]==-1:
                    continue
                if correction_x[i,a]==1:
                    outcome[x_prop,a] = (outcome[x_prop,a]+1)%2
                if correction_x[i,a]==-1:
                    outcome[x_prop,a] = -1
            for z_prop in Z_propagate[pos]:
                if outcome[z_prop,a]==-1:
                    continue
                if correction_z[i,a]==1:
                    outcome[z_prop,a] = (outcome[z_prop,a]+1)%2
                if correction_z[i,a]==-1:
                    outcome[z_prop,a] = -1

    num_errors=0
    for a in range(2):
        flag=1
        for i in range(4):
            if outcome[i,0]==1:
                flag=0
            if outcome[i,0]==-1:
                flag*=0.5
        num_errors+= (1-flag)
    return num_errors

def estimate_prob_0prep_l1(p,num_shots):
    global detector_now, no_ec

    no_ec=False

    N_prev = 1
    N_now = N_c4

    list_detector_0prep=[]
    list_detector_X=[]
    list_detector_Z=[]
    list_detector_m=[]

    detector_now=0

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    detector_0prep = append_noisy_0prep(circuit,0,N_now,N_prev,N_now,p)
    
    sample = circuit.compile_detector_sampler().sample(shots=num_shots)
    
    sample = [x for x in sample if post_selection_c4(x,detector_0prep[0])]
    
    num=len(sample)
    
    post_selection_prob_l1 = 1-num/num_shots
    variance_post_selection_prob_l1 = (num_shots-num)/(num_shots**2)

    return post_selection_prob_l1, variance_post_selection_prob_l1

def estimate_prob_0prep_l2(p,num_shots):
    global detector_now, no_ec

    no_ec=False

    N_prev=N_c4
    N_now=N_c6
    n_now=3

    list_detector_0prep=[]
    list_detector_X=[]
    list_detector_Z=[]
    list_detector_m=[]

    detector_now=0

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    detector_0prep = append_noisy_0prep(circuit,0,N_now,N_prev,N_now,p)
    
    sample = circuit.compile_detector_sampler().sample(shots=num_shots)
    
    for a in range(6):
        sample = [x for x in sample if post_selection_c4(x,detector_0prep[a][0])]
    
    num1=len(sample)
    
    sample = [x for x in sample if post_selection_c6(x,detector_0prep[6])]
    
    num2=len(sample)
    
    post_selection_prob_l2 = 1-num2/num1
    variance_post_selection_prob_l2 = (num1-num2)/(num1**2)

    return post_selection_prob_l2, variance_post_selection_prob_l2

def estimate_prob_edt_l2(p,num_shots):
    global detector_now, no_ec

    no_ec=False

    N_prev=N_c4
    N_now=N_c6
    n_now=3

    list_detector_0prep=[]
    list_detector_X=[]
    list_detector_Z=[]
    list_detector_m=[]

    detector_now=0

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    detector_0prep1 = append_noisy_0prep(circuit,0,2*N_now,N_prev,N_now,p)
    detector_0prep2 = append_noisy_0prep(circuit,1,2*N_now,N_prev,N_now,p)
    
    detector_0prep_c4=[[]]*3
    detector_Z_c4=[[]]*3
    detector_X_c4= [[]]*3
    
    for a in range(3):
        detector_0prep_c4[a], detector_Z_c4[a], detector_X_c4[a] = append_noisy_ec(circuit,(0)*N_prev,(2*N_now)*N_prev,(2*N_now+1)*N_prev,(2*N_now+2)*N_prev,1,N_prev,p)
    
    sample = circuit.compile_detector_sampler().sample(shots=num_shots)
    
    for a in range(6):
        sample = [x for x in sample if post_selection_c4(x,detector_0prep1[a][0])]
        sample = [x for x in sample if post_selection_c4(x,detector_0prep2[a][0])]
    
    for a in range(3):
        sample = [x for x in sample if post_selection_c4(x,detector_0prep_c4[a][0])]
    
    sample = [x for x in sample if post_selection_c6(x,detector_0prep1[6])]
    sample = [x for x in sample if post_selection_c6(x,detector_0prep2[6])]
    
    num1=len(sample)
    
    for a in range(3):
        sample = [x for x in sample if post_selection_c4(x,detector_X_c4[a][0])]
        sample = [x for x in sample if post_selection_c4(x,detector_Z_c4[a][0])]
    
    num2=len(sample)
    
    edt_prob_l2 = 1-num2/num1
    variance_edt_prob_l2 = (num1-num2)/(num1**2)

    return edt_prob_l2, variance_edt_prob_l2

# Estimate the logical error rate of level-1
def estimate_logical_cnot_error_l1(p,num_shots):
    global detector_now, no_ec

    no_ec=False

    N_prev=1
    N_now=N_c4
    
    Q=10

    list_detector_0prep=[]
    list_detector_X=[]
    list_detector_Z=[]
    list_detector_m=[]

    detector_now=0

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    append_0prep(circuit,0,N_prev,N_now)
    append_0prep(circuit,8,N_prev,N_now)
    append_0prep(circuit,16,N_prev,N_now)
    append_0prep(circuit,24,N_prev,N_now)

    append_h(circuit,0,N_prev,N_now)
    append_h(circuit,16,N_prev,N_now)

    append_cnot(circuit,0,8,N_prev,N_now)
    append_cnot(circuit,16,24,N_prev,N_now)

    #error-free CNOT + noisy CNOT (or CZ)+EC gadget

    for q in range(Q):
        append_cnot(circuit, 0, 16,N_prev,N_now)
        
        append_noisy_cnot(circuit, 0, 16,N_prev,N_now, p)

        [detector_0prep, detector_Z, detector_X] = append_noisy_ec(circuit,0,32,40,48,N_prev,N_now, p, -1)
        list_detector_0prep.extend(detector_0prep)
        list_detector_X.append(detector_X)
        list_detector_Z.append(detector_Z)

        [detector_0prep, detector_Z, detector_X] = append_noisy_ec(circuit,16,32,40,48,N_prev,N_now, p, -1)
        list_detector_0prep.extend(detector_0prep)
        list_detector_X.append(detector_X)
        list_detector_Z.append(detector_Z)

    append_cnot(circuit,0,8,N_prev,N_now)
    append_cnot(circuit,16,24,N_prev,N_now)

    append_h(circuit,0,N_prev,N_now)
    append_h(circuit,16,N_prev,N_now)

    list_detector_m.append(append_m(circuit,0,N_prev,N_now))
    list_detector_m.append(append_m(circuit,8,N_prev,N_now))
    list_detector_m.append(append_m(circuit,16,N_prev,N_now))
    list_detector_m.append(append_m(circuit,24,N_prev,N_now))
    
    sample = circuit.compile_detector_sampler().sample(shots=num_shots)

    for a in list_detector_0prep:
        sample=[x for x in sample if post_selection_c4(x,a)]
    
    num=len(sample)

    err = sum([accept_c4(x,list_detector_m,list_detector_X,list_detector_Z,Q) for x in sample])
    
    logical_error_l1=err/(num*Q*2)
    variance_l1=err/(num*Q*2)**2

    return logical_error_l1, variance_l1

# Estimate the logical error rate of level-2 with post-selection
def estimate_logical_cnot_error_l2(p,num_shots):
    global detector_now, no_ec

    no_ec=False

    N_prev=N_c4
    N_now=N_c6
    n_now=3
    
    Q=10

    list_detector_0prep=[]
    list_detector_X=[]
    list_detector_Z=[]
    list_detector_m=[]

    detector_now=0

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    append_noisy_0prep(circuit,0,24,N_prev,N_now,0)
    append_noisy_0prep(circuit,6,24,N_prev,N_now,0)
    append_noisy_0prep(circuit,12,24,N_prev,N_now,0)
    append_noisy_0prep(circuit,18,24,N_prev,N_now,0)

    append_h(circuit,0,N_prev,n_now)
    append_h(circuit,12,N_prev,n_now)

    append_cnot(circuit,0,6,N_prev,n_now)
    append_cnot(circuit,12,18,N_prev,n_now)

    #error-free CNOT + noisy CNOT (or CZ)+EC gadget

    for q in range(Q):
        append_cnot(circuit, 0, 12, N_prev,n_now)
        
        append_noisy_cnot(circuit, 0, 12, N_prev,n_now, p)

        [detector_0prep, detector_Z, detector_X] = append_noisy_ec(circuit,0,24,30,36,N_prev,N_now, p, -1)
        list_detector_0prep.extend(detector_0prep)
        list_detector_X.append(detector_X)
        list_detector_Z.append(detector_Z)

        [detector_0prep, detector_Z, detector_X] = append_noisy_ec(circuit,12,24,30,36,N_prev,N_now, p, -1)
        list_detector_0prep.extend(detector_0prep)
        list_detector_X.append(detector_X)
        list_detector_Z.append(detector_Z)

    append_cnot(circuit,0,6,N_prev,n_now)
    append_cnot(circuit,12,18,N_prev,n_now)

    append_h(circuit,0,N_prev,n_now)
    append_h(circuit,12,N_prev,n_now)

    list_detector_m.append(append_m(circuit,0,N_prev,n_now))
    list_detector_m.append(append_m(circuit,6,N_prev,n_now))
    list_detector_m.append(append_m(circuit,12,N_prev,n_now))
    list_detector_m.append(append_m(circuit,18,N_prev,n_now))
    
    num=0
    err=0
    
    sample = circuit.compile_detector_sampler().sample(shots=num_shots)

    for a in list_detector_0prep:
        if len(a)==1:
            sample=[x for x in sample if post_selection_c4(x,a[0])]
        elif len(a)==2:
            sample=[x for x in sample if post_selection_c4(x,a)]
        elif len(a)==3:
            sample=[x for x in sample if post_selection_c6(x,a)]

    sample=[x for x in sample if accept(x,list_detector_m,list_detector_X,list_detector_Z,Q)!=-1]

    num+=len(sample)

    err+= sum([accept(x,list_detector_m,list_detector_X,list_detector_Z,Q) for x in sample])
    
    logical_error_l2=err/(num*Q*2)
    variance_l2=err/(num*Q*2)**2

    return logical_error_l2, variance_l2

# ---------------------------------------------------------------------------
# Error correction by measuring stabilizers with single-qubit ancillas
# (alternative to Knill's teleportation-based EC; hook errors are not handled)
# ---------------------------------------------------------------------------

# Logical operators of a C4 block, consistent with decode_measurement_c4
ZL_c4 = [[0,2],[2,3]]
XL_c4 = [[0,1],[1,3]]

# C6 stabilizers on the 6 level-1 logical qubits (identical supports for X and Z type)
S_c6 = [[0,1,2,5],[0,3,4,5]]

# Data qubit i of C4 block j is paired with ancilla qubit PERM[j][i] in the transversal CNOT.
# The relabeling acts as a logical gate on the pair, so that ancilla logical 1 accumulates S1
# and ancilla logical 2 accumulates S2.
PERM_Z_CHECK = [[0,3,1,2],[0,1,2,3],[0,2,3,1]]
PERM_X_CHECK = [[0,2,3,1],[0,1,2,3],[0,3,1,2]]

def build_lookup_c6():
    # (erased pair, syndrome change) -> correction on the two level-1 qubits of that pair
    lookup = {}
    for j in range(3):
        for u in range(2):
            for v in range(2):
                flip = [0]*6
                flip[2*j], flip[2*j+1] = u, v
                syndrome = tuple(sum(flip[k] for k in s)%2 for s in S_c6)
                lookup[(j, syndrome)] = (u, v)
    return lookup

LOOKUP_C6 = build_lookup_c6()

def append_noisy_stabilizer_ec_c4(circuit, loc, anc, p):
    # Measure ZZZZ then XXXX on the C4 block at loc, reusing the ancilla qubit anc.
    # Returns the measurement indices [ZZZZ, XXXX].
    circuit.append("R", anc)
    circuit.append("X_ERROR", anc, p)
    for i in range(N_c4):
        circuit.append("CNOT", [loc+i, anc])
        circuit.append("DEPOLARIZE2", [loc+i, anc], p)
    circuit.append("X_ERROR", anc, p)
    m_z = circuit.num_measurements
    circuit.append("M", anc)

    circuit.append("R", anc)
    circuit.append("X_ERROR", anc, p)
    circuit.append("H", anc)
    for i in range(N_c4):
        circuit.append("CNOT", [anc, loc+i])
        circuit.append("DEPOLARIZE2", [anc, loc+i], p)
    circuit.append("H", anc)
    circuit.append("X_ERROR", anc, p)
    m_x = circuit.num_measurements
    circuit.append("M", anc)

    return [m_z, m_x]

def append_noisy_c4_block_prep(circuit, loc, p, basis='z'):
    # |00> (basis='z') or |++> (basis='x') of the C4 block at loc
    for i in range(N_c4):
        circuit.append("R", loc+i)
        circuit.append("X_ERROR", loc+i, p)
    circuit.append("H", loc)
    for i in range(1, N_c4):
        circuit.append("CNOT", [loc, loc+i])
        circuit.append("DEPOLARIZE2", [loc, loc+i], p)
    if basis == 'x':
        for i in range(N_c4):
            circuit.append("H", loc+i)

def append_noisy_c4_block_m(circuit, loc, p, basis='z'):
    # Transversal measurement of the C4 block at loc. Returns the index of the first measurement.
    if basis == 'x':
        for i in range(N_c4):
            circuit.append("H", loc+i)
    for i in range(N_c4):
        circuit.append("X_ERROR", loc+i, p)
    m_start = circuit.num_measurements
    for i in range(N_c4):
        circuit.append("M", loc+i)
    return m_start

def append_noisy_stabilizer_ec_c6(circuit, loc, anc_block, anc, p):
    # Level-1 EC on the three C4 blocks of the C6 block at loc, then the C6 checks:
    # S1 and S2 are collected on the two logical qubits of one ancilla C4 block.
    record = {'c4': [append_noisy_stabilizer_ec_c4(circuit, loc+N_c4*j, anc, p) for j in range(3)]}

    for basis, perm in (('z', PERM_Z_CHECK), ('x', PERM_X_CHECK)):
        append_noisy_c4_block_prep(circuit, anc_block, p, basis)
        record['anc_ec_'+basis] = append_noisy_stabilizer_ec_c4(circuit, anc_block, anc, p)
        for j in range(3):
            for i in range(N_c4):
                data_qubit = loc+N_c4*j+i
                anc_qubit = anc_block+perm[j][i]
                if basis == 'z':
                    circuit.append("CNOT", [data_qubit, anc_qubit])
                else:
                    circuit.append("CNOT", [anc_qubit, data_qubit])
                circuit.append("DEPOLARIZE2", [data_qubit, anc_qubit], p)
        record[basis] = append_noisy_c4_block_m(circuit, anc_block, p, basis)

    return record

def decode_c4_block(sample, m_start, basis='z'):
    # Vectorized over shots: logical values of a measured C4 block and whether its parity check failed
    m = sample[:, m_start:m_start+N_c4].astype(int)
    L = ZL_c4 if basis == 'z' else XL_c4
    logical = np.stack([m[:, L[0]].sum(1)%2, m[:, L[1]].sum(1)%2], axis=1)
    detected = m.sum(1)%2 == 1
    return logical, detected

def count_logical_errors(outcome):
    # outcome: (shots, 4 blocks, 2 logicals) with -1 for erased; same weighting as accept()
    num_errors = np.zeros(outcome.shape[0])
    for a in range(2):
        flag = np.ones(outcome.shape[0])
        flag[(outcome[:, :, a] == 1).any(1)] = 0
        flag *= 0.5**(outcome[:, :, a] == -1).sum(1)
        num_errors += 1-flag
    return num_errors

# Estimate the logical error rate of level-1 with stabilizer-measurement EC
def estimate_logical_cnot_error_l1_stabilizer(p,num_shots):
    N_prev=1
    N_now=N_c4

    Q=10

    loc = [0, 4, 8, 12]   # data 1, reference 1, data 2, reference 2
    anc = 16

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    for l in loc:
        append_0prep(circuit,l,N_prev,N_now)
    append_h(circuit,loc[0],N_prev,N_now)
    append_h(circuit,loc[2],N_prev,N_now)
    append_cnot(circuit,loc[0],loc[1],N_prev,N_now)
    append_cnot(circuit,loc[2],loc[3],N_prev,N_now)

    #error-free CNOT + noisy CNOT+EC gadget
    list_syndrome=[]
    for q in range(Q):
        append_cnot(circuit,loc[0],loc[2],N_prev,N_now)
        append_noisy_cnot(circuit,loc[0],loc[2],N_prev,N_now,p)
        list_syndrome.extend(append_noisy_stabilizer_ec_c4(circuit,loc[0],anc,p))
        list_syndrome.extend(append_noisy_stabilizer_ec_c4(circuit,loc[2],anc,p))

    append_cnot(circuit,loc[0],loc[1],N_prev,N_now)
    append_cnot(circuit,loc[2],loc[3],N_prev,N_now)
    append_h(circuit,loc[0],N_prev,N_now)
    append_h(circuit,loc[2],N_prev,N_now)
    list_m=[append_noisy_c4_block_m(circuit,l,0) for l in loc]

    sample = circuit.compile_sampler().sample(shots=num_shots)

    # C4 only detects errors: post-select on all syndromes being trivial
    sample = sample[~sample[:, list_syndrome].any(1)]
    num=len(sample)

    outcome = np.zeros([num,4,2])
    for i, m_start in enumerate(list_m):
        logical, detected = decode_c4_block(sample, m_start)
        outcome[:, i, :] = logical
        outcome[detected, i, :] = -1

    err = count_logical_errors(outcome).sum()

    logical_error_l1=err/(num*Q*2)
    variance_l1=err/(num*Q*2)**2

    return logical_error_l1, variance_l1, num/num_shots

# Estimate the logical error rate of level-2 with stabilizer-measurement EC and lookup-table decoding
def estimate_logical_cnot_error_l2_stabilizer(p,num_shots):
    global detector_now

    detector_now=0

    N_prev=N_c4
    N_now=N_c6
    n_now=3

    Q=10

    loc = [0, 6, 12, 18]   # in units of C4 blocks: data 1, reference 1, data 2, reference 2
    anc_block = 30*N_c4
    anc = 31*N_c4

    circuit = stim.Circuit()

    #Prepare ideal Bell pairs
    for l in loc:
        append_noisy_0prep(circuit,l,24,N_prev,N_now,0)
    append_h(circuit,loc[0],N_prev,n_now)
    append_h(circuit,loc[2],N_prev,n_now)
    append_cnot(circuit,loc[0],loc[1],N_prev,n_now)
    append_cnot(circuit,loc[2],loc[3],N_prev,n_now)

    #error-free CNOT + noisy CNOT+EC gadget
    list_record=[]
    for q in range(Q):
        append_cnot(circuit,loc[0],loc[2],N_prev,n_now)
        append_noisy_cnot(circuit,loc[0],loc[2],N_prev,n_now,p)
        list_record.append([append_noisy_stabilizer_ec_c6(circuit,l*N_c4,anc_block,anc,p) for l in (loc[0], loc[2])])

    append_cnot(circuit,loc[0],loc[1],N_prev,n_now)
    append_cnot(circuit,loc[2],loc[3],N_prev,n_now)
    append_h(circuit,loc[0],N_prev,n_now)
    append_h(circuit,loc[2],N_prev,n_now)
    list_m=[[append_noisy_c4_block_m(circuit,(l+j)*N_c4,0) for j in range(3)] for l in loc]

    sample = circuit.compile_sampler().sample(shots=num_shots)
    shots = len(sample)

    # Round-by-round decoding of each data block, tracking a Pauli frame on the level-1 qubits.
    # basis 'z' checks find X errors (frame_x), basis 'x' checks find Z errors (frame_z).
    reject = np.zeros(shots, dtype=bool)
    frame = {(b, basis): np.zeros([shots,6], dtype=int) for b in range(2) for basis in 'zx'}
    for b in range(2):
        for basis, c4_index in (('z',0), ('x',1)):
            prev_c4 = np.zeros([shots,3], dtype=bool)
            prev_syndrome = np.zeros([shots,2], dtype=int)
            for q in range(Q):
                record = list_record[q][b]
                c4_syndrome = sample[:, [record['c4'][j][c4_index] for j in range(3)]]
                erased = c4_syndrome != prev_c4
                prev_c4 = c4_syndrome

                # Discard if the ancilla block was prepared with a detected error. A failed parity check
                # in the ancilla readout is not a reason to discard: data errors are copied onto the
                # ancilla block, which is how they are detected.
                reject |= sample[:, record['anc_ec_'+basis]].any(1)
                syndrome, _ = decode_c4_block(sample, record[basis], basis)

                change = syndrome ^ prev_syndrome
                prev_syndrome = syndrome
                has_change = change.any(1)
                num_erased = erased.sum(1)
                reject |= has_change & (num_erased != 1)

                for j in range(3):
                    for s in ((0,1),(1,0),(1,1)):
                        hit = has_change & (num_erased == 1) & erased[:, j] & (change[:,0] == s[0]) & (change[:,1] == s[1])
                        u, v = LOOKUP_C6[(j, s)]
                        frame[(b, basis)][hit, 2*j] ^= u
                        frame[(b, basis)][hit, 2*j+1] ^= v

    keep = ~reject
    sample = sample[keep]
    num = len(sample)

    # Level-1 readout of the four blocks, then apply the frame: an X error on a data block flips
    # its reference block, a Z error on a data block flips the data block itself (after the final H)
    level1 = np.zeros([num,4,6], dtype=int)
    erased = np.zeros([num,4,3], dtype=bool)
    for i in range(4):
        for j in range(3):
            logical, detected = decode_c4_block(sample, list_m[i][j])
            level1[:, i, 2*j:2*j+2] = logical
            erased[:, i, j] = detected
    for b in range(2):
        level1[:, 2*b+1, :] ^= frame[(b,'z')][keep]
        level1[:, 2*b, :] ^= frame[(b,'x')][keep] @ FINAL_H_Z_FLIP % 2

    outcome = np.zeros([num,4,2])
    for s in range(num):
        for i in range(4):
            M = [-1 if erased[s,i,k//2] else level1[s,i,k] for k in range(6)]
            outcome[s,i,:] = decode_measurement_c6(M)

    err = count_logical_errors(outcome).sum()

    logical_error_l2=err/(num*Q*2)
    variance_l2=err/(num*Q*2)**2

    return logical_error_l2, variance_l2, num/shots

# Row k: level-1 readout bits of a data block flipped by a Z error on its level-1 qubit k,
# after the final logical H (up to C6 stabilizers)
FINAL_H_Z_FLIP = np.array([[0,0,1,0,0,1],
                           [0,0,0,1,1,1],
                           [0,0,1,1,0,0],
                           [0,0,1,0,0,0],
                           [0,0,0,0,1,1],
                           [0,0,0,0,1,0]])

if __name__ == '__main__':
    output_file_name = str(sys.argv[1])
    num_shots = int(sys.argv[2])
    case_number = int(sys.argv[3])
    p = float(sys.argv[4])
    error_model = str(sys.argv[5])
    l = int(sys.argv[6])
    ec_method = str(sys.argv[7]) if len(sys.argv) > 7 else 'knill'

    if error_model == 'a':
        gamma = p/10
    elif error_model == 'b':
        gamma = p/2
    elif error_model == 'c':
        gamma = p

    N_c4=4
    N_c6=6

    check_matrix = [[1, 1, 1, 1]]
    if l!=1 and l!=2:
        print('l should be 1 or 2!')
    elif ec_method!='knill' and ec_method!='stabilizer':
        print('ec_method should be knill or stabilizer!')
    else:
        acceptance = None
        if ec_method=='knill':
            if l==1:
                logical_error, variance = estimate_logical_cnot_error_l1(p,num_shots)
            elif l==2:
                logical_error, variance = estimate_logical_cnot_error_l2(p,num_shots)
        else:
            if l==1:
                logical_error, variance, acceptance = estimate_logical_cnot_error_l1_stabilizer(p,num_shots)
            elif l==2:
                logical_error, variance, acceptance = estimate_logical_cnot_error_l2_stabilizer(p,num_shots)
        with open(output_file_name, 'a') as file:
            output_data = {
                'physical_error': p,
                'logical_error': logical_error,
                'variance': variance
            }
            if acceptance is not None:
                output_data['acceptance'] = acceptance
            file.write('\"case' + str(case_number) + '\":' + json.dumps(output_data) +',\n')
        