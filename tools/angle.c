#include <stdio.h>
#include <math.h>

#define PI 3.14159265358979323846 //this kind of accuracy is 100% NEEDED

float calc_angle(int i1, int q1, int i2, int q2){
    float res, angle_1, angle_2;
    
    angle_1 = atan2f(q1,i1);
    angle_2 = atan2f(q2,i2);
    
    res = angle_1 - angle_2;
    
    printf("Angle1: %f, Angle2: %f, Result: %f \r\n",angle_1,angle_2,res);
    
    return res;
    
}

int main(){
    float angle_rad, angle_deg;
    angle_rad = calc_angle(1,1,-1,-1); //parameters are i1,q1,i2,q2
    angle_deg = (180/PI)*angle_rad;

    printf("Angle is : %f radians, %f degrees",angle_rad,angle_deg);

    return 0;
}
