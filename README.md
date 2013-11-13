#Sort-em#

###Documentation#
Sort-em is a small Python program that utilizes a SQLite database to catalog all files in a given directory along with a SHA512 checksum. Once the initial scan is complete and the database has been fully populated, all files are inspected for duplicates.

Once the script has completed, each file record in the database will now be marked with a master or duplicate flag.

###Latest Version#
Details of the latest version can be found on my blog project page under http://blaynecampbell.com/sort-em/

###Usage#
Make sortem.py executable:
```
chmod +x sortem.py
```
Execute:
```
python sortem.py
```
#
######NOTES:#
__If a database already exists with the same name, Sort-em will ask if you would like to move duplicates__

*See multiple database configuration in sortem.py*

__The program will prompt for the ABSOLUTE PATH to the directory of which you would like to index.__

*Press ENTER to accept the default path (current_directory/files)*

__Specify if you would like the duplicate files to be moved to the 'duplicates' directory.__

*Default is NO. Duplicate files are always logged in the working directory (duplicates.log)*
***
The program may take a long period of time to complete depending on the number & size of files being processed.

Once the process has completed, you will have a database file containing all file information as well as which files were detected as duplicates via SHA512 checksum.

###Licensing
Please see the file called LICENSE.
