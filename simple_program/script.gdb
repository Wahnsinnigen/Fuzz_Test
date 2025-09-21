# script.gdb
break main                   
run                          
print &str                   
x/s str                      
set *(char*)0x555555558010 = 'h'  
print str                    

