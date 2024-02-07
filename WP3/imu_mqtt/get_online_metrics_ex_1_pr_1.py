import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def get_metrics(imu1,imu2,imu3,imu4):
    
   print(" imu1 ", len(imu1), " imu2 ", len(imu2), " imu3 ", len(imu3), " imu4 ", len(imu4)) 
   if(len(imu1) > 0):
      print(len(imu1))
    #for item in imu1:
    #    print(item)
    #   return(imu1)	
   create_plots(imu1, imu2, imu3, imu4)

def create_plots(imu1, imu2, imu3, imu4):
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []
    time1 = []
    W1 = []
    X1 = []
    Y1 = []
    Z1 = []
    time2 = []
    W2 = []
    X2 = []
    Y2 = []
    Z2 = []
    time3 = []
    W3 = []
    X3 = []
    Y3 = []
    Z3 = []
    time4 = []
    W4 = []
    X4 = []
    Y4 = []
    Z4 = []
    if len(imu2) > 0 or len(imu1) > 0 or len(imu3) > 0 or len(imu4) > 0:
      for i in range(len(imu1)):
         if( i > 0):    
            item = imu1[i].replace('[', '').replace(']', '').replace('"', '')
            data = item.split()
            time1.append(float(data[4]))  
            W1.append(float(data[5]))     
            X1.append(float(data[6]))     
            Y1.append(float(data[7]))    
            Z1.append(float(data[8]))  
      for i in range(len(imu2)):
         if( i > 0):    
            item = imu2[i].replace('[', '').replace(']', '').replace('"', '')
            data = item.split()
            time2.append(float(data[4]))  
            W2.append(float(data[5]))     
            X2.append(float(data[6]))     
            Y2.append(float(data[7]))    
            Z2.append(float(data[8]))  
      for i in range(len(imu3)):
         if( i > 0):    
            item = imu3[i].replace('[', '').replace(']', '').replace('"', '')
            data = item.split()
            time3.append(float(data[4]))  
            W3.append(float(data[5]))     
            X3.append(float(data[6]))     
            Y3.append(float(data[7]))    
            Z3.append(float(data[8]))  
      for i in range(len(imu4)):
         if( i > 0):    
            item = imu4[i].replace('[', '').replace(']', '').replace('"', '')
            data = item.split()
            time4.append(float(data[4]))  
            W4.append(float(data[5]))     
            X4.append(float(data[6]))     
            Y4.append(float(data[7]))    
            Z4.append(float(data[8]))  
       

    imu1List.append(time1)
    imu1List.append(W1)
    imu1List.append(X1)
    imu1List.append(Y1)
    imu1List.append(Z1)
    imu2List.append(time2)
    imu2List.append(W2)
    imu2List.append(X2)
    imu2List.append(Y2)
    imu2List.append(Z2)
    imu3List.append(time3)
    imu3List.append(W3)
    imu3List.append(X3)
    imu3List.append(Y3)
    imu3List.append(Z3)
    imu4List.append(time4)
    imu4List.append(W4)
    imu4List.append(X4)
    imu4List.append(Y4)
    imu4List.append(Z4)

    fig, axs = plt.subplots(4, 1, figsize=(8, 10))  # Adjust figsize as needed
    
    # Plot imu1 data
    axs[0].plot(imu1List[0], imu1List[1], label='W1')
    axs[0].plot(imu1List[0], imu1List[2], label='X1')
    axs[0].plot(imu1List[0], imu1List[3], label='Y1')
    axs[0].plot(imu1List[0], imu1List[4], label='Z1')
    axs[0].set_title('IMU 1')
    axs[0].legend()

    # Plot imu2 data
    axs[1].plot(imu2List[0], imu2List[1], label='W2')
    axs[1].plot(imu2List[0], imu2List[2], label='X2')
    axs[1].plot(imu2List[0], imu2List[3], label='Y2')
    axs[1].plot(imu2List[0], imu2List[4], label='Z2')
    axs[1].set_title('IMU 2')
    axs[1].legend()

    # Plot imu3 data
    axs[2].plot(imu3List[0], imu3List[1], label='W3')
    axs[2].plot(imu3List[0], imu3List[2], label='X3')
    axs[2].plot(imu3List[0], imu3List[3], label='Y3')
    axs[2].plot(imu3List[0], imu3List[4], label='Z3')
    axs[2].set_title('IMU 3')
    axs[2].legend()

    # Plot imu4 data
    axs[3].plot(imu4List[0], imu4List[1], label='W4')
    axs[3].plot(imu4List[0], imu4List[2], label='X4')
    axs[3].plot(imu4List[0], imu4List[3], label='Y4')
    axs[3].plot(imu4List[0], imu4List[4], label='Z4')
    axs[3].set_title('IMU 4')
    axs[3].legend()

    # Adjust layout
    plt.tight_layout()

    # Save or show the plot
    currentTime = datetime.now()
    currentTime = currentTime.strftime("%Y-%m-%d_%H:%M:%S")
    fileName = f"{currentTime}.png" 
    plt.savefig(fileName)  # Save the plot
    # plt.show()



																																	
