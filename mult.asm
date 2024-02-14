# Multiply R0 and R1 together and store result in R2
# Load starting at 50
DATA  R3, 1
XOR   R2, R2
CLF              
SHR   R0         
JC    59      
JUMP  61       
CLF              
ADD   R1,R2       
CLF             
SHL   R1       
SHL   R3    
JC    68          
JUMP  53
END     