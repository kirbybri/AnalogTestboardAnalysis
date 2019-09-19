Analog Test Board Standard Data Taking Process
===================================================

Configuration
-------------
Check board is assembled and cabled correctly following instructions at X.

Turn on board, verify current draw is normal,and that "Clock OK" LED is on.

Program the clock using "programClockChip.py", verify that it is successful.

Start GUI using "testBoard.py", if timeout error try reseating USB cable

Press GUI “Configure All” button, wait until configuration process completes

Press GUI “Check Link Ready” button. If the link is not ready, reseat fibre cable and try again, repeat as necessary

In GUI "Trigger" tab, press “Select Calibration Pulses” button ONCE

In GUI “Control” tab, press “Trigger and Take Samples” button and make sure a reasonable waveform is displayed

Pedestal runs
-------------
Power off board and disconnect jumper from channel inputs

-ensure # of samples is suitably large (4093?)
-press pedestal buttong
-hit take samples
-close GUI

Pulser runs
-connect jumper to appropriate channel input
-ensure # of samples is suitably large (4093?)

LAUROC1 Ch1 pulsed
LAUROC2 Ch2 pulsed
1x pedestal
4x pedestal 
