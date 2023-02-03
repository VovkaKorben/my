import re
import time

re_float = re.compile(r'[-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?')


def is_int(s):
    try:
        i = int(s)
    except ValueError:
        return False
    else:
        return True


def is_float(s):
    matches = re_float.match(s)
    if matches == None:
        return False
    return (matches.span()[1] == len(s))


def utc_ms(add_time: int = 0):
    return (time.time_ns()//1000000)+add_time

"""
!AIVDM,2,1,9,B,53nFBv01SJ<thHp6220H4heHTf2222222222221?50:454o<`9QSlUDp,0*09
!AIVDM,2,2,9,B,888888888888880,2*2E
!AIVDM,2,1,6,B,56:fS:D0000000000008v0<QD4r0`T4v3400000t0`D147?ps1P00000,0*3D
!AIVDM,2,2,6,B,000000000000008,2*29
!AIVDM,2,1,8,A,53Q6SR02=21U`@H?800l4E9<f1HTLt000000001?BhL<@4q30Glm841E,0*7C
!AIVDM,2,2,8,A,1DThUDQh0000000,2*4D
!AIVDM,1,1,,B,133UQ650000>gOhMGl0Sh1nH0d4D,0*33

IIICSI

i = can be int 
I = must be int

iii

"""