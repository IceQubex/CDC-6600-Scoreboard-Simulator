# CDC-6600-Scoreboard-Simulator
A program which simulates the CDC 6600 Scoreboard, which is able to implement dynamic scheduling of MIPS instructions. 

The project was done in Python, and the final file is named as “simulator.py”. No additional external libraries were utilized for this project (the inbuilt sys library was included to be able to parse the command-line arguments). 

The following lists 2 possible methods to execute the simulation program. 
## Method 1 – Utilizing the Makefile:

The program can also be executed by using the Makefile. The Makefile defines 5 options, as follows:
1. make run_default

	This option will execute the simulation program using the default instruction set files which were included as part of the project document. These input files are located in the default folder.

2. make run_test1

	This option will execute the simulation program using the Test Case 1 files. These input files are located in the test_case_1 folder.

3. make run_test2

	This option will execute the simulation program using the Test Case 2 files. These input files are located in the test_case_2 folder.

4. make run_test3

	This option will execute the simulation program using the Test Case 3 files. These input files are located in the test_case_3 folder.

5.	make clean

	This option will delete the result.txt file, cleaning the directory and leaving only the necessary files for executing the program.
Executing the simulation program through the Makefile will create a result.txt file with the output in the same directory as the simulation.py program. 
 
## Method 2 – Directly from the Command-line with custom configuration and data files:

The program can be run directly from the command-line, by passing in the 4 necessary arguments as follows in the command-line:
`python3 ./simulator.py <inst_file.txt> <data_file.txt> <config_file.txt> <result_file.txt>`
	
The above command will use the first 3 arguments `<inst_file.txt>, <data_file.txt> & <config_file.txt>` to set up and run the scoreboard simulation, and then produce an output in the `<result_file.txt>` file defined in the 4th argument. 

