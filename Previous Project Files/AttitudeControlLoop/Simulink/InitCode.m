close all
clear all
clc

%create a new instance of STK11
uiapp = actxserver('STK12.Application');
uiapp.visible = 1;

%get the object model root for STK12, IAgStkObjectRoot 
root = uiapp.Personality2;

root.LoadScenario('C:\Users\gcorrao\OneDrive - ANSYS, Inc\AGI\09-Trainings\Integration Training\Automation\Simulink\AttitudeControlLoop\STK Scenario\Attitude_Control.sc');
objSat=root.GetObjectFromPath('/Satellite/True');
objRef=root.GetObjectFromPath('/Satellite/Reference');

%reset the scenario
root.ExecuteCommand('Animate * Reset');

%store the STK parameters
stkParams = cell(4,1);
stkParams{1} = uiapp;
stkParams{2} = root;
stkParams{3} = objSat;
stkParams{4} = objRef;

set_param(gcb, 'UserData', stkParams);

root.ExecuteCommand('SetUnits / EpSec');
root.UnitPreferences.SetCurrentUnit('DateFormat', 'EpSec');

