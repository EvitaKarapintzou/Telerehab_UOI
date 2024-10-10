from shared_variables import imus

# def read_configure_file():
#     global imus
#     with open('configure.txt', 'r') as file:
#         content = file.read()
#         lines = content.splitlines()
#         for line in lines:
#             parts = line.split()
#             if(parts[0] == 'IMU'):
#                 imus.extend(parts[1:]) 
LIMU1 = 'FEAC84C53DE7'
LIMU2 = 'E25AD03D0194'
LIMU3 = 'C8925E7DC6BD'
LIMU4 = 'E15561CB9161'

def read_configure_file():
    global imus, Limu1, Limu2, Limu3, Limu4
    with open('configure.txt', 'r') as file:
        content = file.read()
        lines = content.splitlines()
        for line in lines:
            parts = line.split()
            if parts[0] == 'IMU':
                imus.extend(parts[1:])

                if len(parts) > 1:
                    Limu1 = parts[1]
                if len(parts) > 2:
                    Limu2 = parts[2]
                if len(parts) > 3:
                    Limu3 = parts[3]
                if len(parts) > 4:
                    Limu4 = parts[4]
                    
read_configure_file()
                    
