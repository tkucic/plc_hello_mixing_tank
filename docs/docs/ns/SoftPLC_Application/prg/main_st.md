# Hello Mixing tank | [MAIN] | [NAMESPACES] | [METRICS] | [BACK]  

## Documentation for Program main  

```pascal
INTERFACE
    VAR
        vMode : MODES; (*Variable to keep track of system mode Manual/Auto*)
        vModeOld : MODES; (*Memory of last mode*)
        vAutoState : AUTO_SEQUENCE; (*Variable to track the automatic sequence*)
        MixingTimer : TON; (*Timer to control the mixing duration*)
    END_VAR
END_INTERFACE
PROGRAM main:
    (*Functional description:
There are two ways of operation:
	- Manual
	- Automatic
Manual:
	- Operator is able to operate each valve manually
	- Operator is able to operate the mixer motor manually
	- Overfill protections are disabled
	- Operator is able to put the system to auto
	
Automatic:
	- Program will automatically control the valves and the mixing motor if system is in auto
	- If the tanks level is undefined it assumes draining state
	- In draining state, drains the tank until LS02 activates (tank is empty)
	- When tank is empty, it activates the medium 1 and 2 valves, closes the drain valve and the tank is filling up
	- Filling state is until LS01 is activated (Tank is full)
	- Then the mixer motor is mixing for 10 seconds
	- After mixing is completed, drain the whole contents
	- Repeats as long as auto is activated
	
HMI Requirements:
	- Manual / Auto needs to be correctly controlled and displayed
	- If manual, clicking on devices activates or stops them
	- If auto, clicking is not doing anything
	- If auto, system is counting number of cycles completed
	- Devices must clearly display if they are activated or deactivated*)

(*Enabling operator to select auto or manual mode*)
CASE vMode OF
	MODES.AUTO:
		IF HMI.SetToManual THEN
			vMode := Modes.MANUAL;
			HMI.SetToManual := FALSE;
		END_IF
		
	MODES.MANUAL:
		IF HMI.SetToAuto THEN
			vMode := Modes.AUTO;
			HMI.SetToAuto := FALSE;
		END_IF
END_CASE

(*Control of the system*)
CASE vMode OF
	MODES.MANUAL: (*Manual*)
		(*On entry do:*)
		IF vMode <> vModeOld THEN
			vAutoState := AUTO_SEQUENCE.DRAINING;
			vModeOld := vMode;
		END_IF
		
		(*In manual, HMI commands are connected to the IO for starting and stopping the devices*)
		(*Commands are implemented with a latch*)
		IO.xDO_M1_MixerMotorRunCmd := (HMI.MixerRunCmd OR IO.xDI_M1_MixerMotorRunning) AND NOT (HMI.MixerStopCmd);
		IO.xDO_VV01_Medium1_OpenCmd := (HMI.Medium1OpenCmd OR IO.xDI_VV01_Medium1_Opened) AND NOT (HMI.Medium1CloseCmd);
		IO.xDO_VV02_Medium2_OpenCmd := (HMI.Medium2OpenCmd OR IO.xDI_VV02_Medium2_Opened) AND NOT (HMI.Medium2CloseCmd);
		IO.xDO_VV03_TankDrain_OpenCmd := (HMI.DrainOpenCmd OR IO.xDI_VV03_TankDrain_Opened) AND NOT (HMI.DrainCloseCmd);
	
	MODES.AUTO: (*Automatic*)
		(*On entry do:*)
		IF vMode <> vModeOld THEN
			vAutoState := AUTO_SEQUENCE.DRAINING;
			vModeOld := vMode;
		END_IF
		CASE vAutoState OF
			AUTO_SEQUENCE.FILLING:
				(*Make sure other devices are not working*)
				IO.xDO_M1_MixerMotorRunCmd := FALSE;
				IO.xDO_VV03_TankDrain_OpenCmd := FALSE;
				
				(*Open both medium valves and start filling the tank*)
				IO.xDO_VV01_Medium1_OpenCmd := NOT IO.xDI_LS01_TankLevelFull;
				IO.xDO_VV02_Medium2_OpenCmd := NOT IO.xDI_LS01_TankLevelFull;
				
				(*When tank is full, wait for the filling valves to close and then go to mixing state*)
				IF IO.xDI_LS01_TankLevelFull AND NOT (IO.xDI_VV01_Medium1_Opened OR IO.xDI_VV02_Medium2_Opened) THEN
					vAutoState := AUTO_SEQUENCE.MIXING;
				END_IF
			AUTO_SEQUENCE.MIXING:
				(*Make sure other devices are not working*)
				IO.xDO_VV01_Medium1_OpenCmd := FALSE;
				IO.xDO_VV02_Medium2_OpenCmd := FALSE;
				IO.xDO_VV03_TankDrain_OpenCmd := FALSE;
				
				(*Start the mixer motor and mix for 10s*)
				IO.xDO_M1_MixerMotorRunCmd := TRUE;
				MixingTimer(IN:=IO.xDI_M1_MixerMotorRunning, PT:=T#10S);
				
				(*When timer has elapsed 10s, wait for motor to stop running, then go to draining*)
				IF MixingTimer.Q THEN
					IO.xDO_M1_MixerMotorRunCmd := FALSE;
					vAutoState := AUTO_SEQUENCE.DRAINING;
				END_IF
				
			AUTO_SEQUENCE.DRAINING:
				(*Make sure other devices are not working*)
				IO.xDO_M1_MixerMotorRunCmd := FALSE;
				IO.xDO_VV01_Medium1_OpenCmd := FALSE;
				IO.xDO_VV02_Medium2_OpenCmd := FALSE;
				
				(*Open the drain valve and start draining the tank*)
				IO.xDO_VV03_TankDrain_OpenCmd := NOT IO.xDI_LS02_TankLevelEmpty;
				
				(*When the tank is empty, wait for the drain valve to close,then go to filling*)
				IF IO.xDI_LS02_TankLevelEmpty AND NOT IO.xDI_VV03_TankDrain_Opened THEN
					vAutoState := AUTO_SEQUENCE.FILLING;
					HMI.CyclesCompleted := HMI.CyclesCompleted + 1;
				END_IF
		END_CASE
END_CASE

(*Command sanity reset*)
IF IO.xDI_M1_MixerMotorRunning THEN
	HMI.MixerRunCmd := FALSE;
ELSE
	HMI.MixerStopCmd := FALSE;
END_IF
IF IO.xDI_VV01_Medium1_Opened THEN
	HMI.Medium1OpenCmd := FALSE;
ELSE
	HMI.Medium1CloseCmd := FALSE;
END_IF
IF IO.xDI_VV02_Medium2_Opened THEN
	HMI.Medium2OpenCmd := FALSE;
ELSE
	HMI.Medium2CloseCmd := FALSE;
END_IF
IF IO.xDI_VV03_TankDrain_Opened THEN
	HMI.DrainOpenCmd := FALSE;
ELSE
	HMI.DrainCloseCmd := FALSE;
END_IF

(*HMI *)
HMI.MotorRotating := HMI.MotorRotating + 2 * BOOL_TO_REAL(IO.xDI_M1_MixerMotorRunning);
IF HMI.MotorRotating >= 360 THEN HMI.MotorRotating := 0; END_IF
HMI.InAuto := vMode = MODES.AUTO;
HMI.InManual := vMode = MODES.MANUAL;
END_PROGRAM
```

## Metrics  

| VAR_IN | VAR_OUT | VAR_IN_OUT | VAR_LOCAL | VAR_EXTERNAL | VAR_GLOBAL | VAR_ACCESS | VAR_TEMP |
| ------ | ------- | ---------- | --------- | ------------ | ---------- | ---------- | -------- |
| 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |

| Actions | Lines of code | Maintainable size |
| ------- | ------------- | ----------------- |
| 0 | 138 | 142 |

---
Autogenerated with [ia_tools](https://github.com/tkucic/ia_tools)  

[MAIN]: ../../../../index_st.md
[NAMESPACES]: ../../nsList_st.md
[METRICS]: ../../../metrics_st.md
[BACK]: ../nsMain_st.md
