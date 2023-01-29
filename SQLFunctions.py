#!/usr/bin/python
import sqlite3



#Helper function to auto construct queries for an insert into statement, creating new entries in a table
def SQLCreateEntry(TableName, Values):
    #Initialize return value 0 indicates success
    ReturnVal = 0
    #connect to our database, hardcoded as saves.db
    LibraryConnection = sqlite3.connect('saves.db')
    #On Connection success
    if LibraryConnection:
        #Initialize our cursor for later function calls
        Cursor = LibraryConnection.cursor()
        #Initialize our SQL query
        Query = "INSERT INTO " + TableName + " ("
        #Initialize the data portion of our sql query
        Data = "VALUES ("
        #For each column that's specified in our passed in Values
        for ColumnName in Values:
            #Our query gets extended with the column name
            #Final format of our query is going to be:
            #INSERT INTO { Table } ({column 1}, {column 2}, ...) VALUES ({ Data 1 }, { Data 2 }, ...) 
            Query += str(ColumnName) + ","
            #We have to denote strings with 's for proper SQL formatting
            if type(Values[ColumnName]) == str:
                Data += "'" + Values[ColumnName] + "',"
            #We have to convert all non strings to strings, to prevent errors in our concatenation
            else:
                Data += str(Values[ColumnName]) + ','
        #We take our query and remove the last character, a comma (,) since we appended commas to every column
        #We also add our closing parentheses
        Query = Query[0:-1] + ')'
        Data = Data[0:-1] + ')'
        #Combine our initial creation query with our data we're inserting into the table
        #Use a newline character just for ease of reading during troubleshooting
        Query += '\n' + Data
        #Execute our finalized query, commit to the database and close it.
        LibraryConnection.execute(Query)
        LibraryConnection.commit()
        LibraryConnection.close()
    #error from database connection
    #extremely unlikely to occur (at least in single-threaded mode, unsure of behavior in multithreading)
    else:
        print("ERROR: SQLite Database Connection error")
        ReturnVal = 1
    return ReturnVal

#Helper function to construct queries for getting data from our SQLite Database
#returns a list of dictionaries for ease of use within our other python code while keeping keys in-tact for each individual row
def SQLGetEntry(TableName, Restrictions, DesiredColumns):
    #Initialize our library connection and our return value
    LibraryConnection = sqlite3.connect('saves.db')
    ReturnList = []
    #On connection success
    if LibraryConnection:
        #Initialize our query
        Query = ''
        #Check if we specify specific columns we want
        if DesiredColumns != []:
            #if we do have specific columns specified
            Query = 'SELECT '
            #Constructing our query with each column name that was passed in
            for column in DesiredColumns:
                Query += column + ', '
            #remove the last comma and space from the query, and add a space
            Query = Query[0:-2] + ' '
            #Create our from query
            Query += 'FROM ' + TableName
        else:
            #If we don't specify specific columns, we get all the columns using the * character
            Query = 'SELECT * FROM ' + TableName
        #If we have restrictions in place
        if Restrictions != {}:
            #modify the query with our where clause creation
            Query += '\n'
            Query += 'WHERE '
            #Construct the where clause from our columns and restriction values
            #NOTE this assumes restrictions will be based on an equal value, not based on other comparisons
            #This is due to the general idea that we will only want values for specific AppIDs and ClientIDs
            #May modify later to allow other comparisons, but not a priority
            for ColumnName in Restrictions:
                #Must denote strings with 's
                if type(Restrictions[ColumnName]) == str:
                    Query += ColumnName + " = '" + Restrictions[ColumnName] + "' AND "
                #Must convert non-strings to strings for concatenation
                else:
                    Query += ColumnName + ' = ' + str(Restrictions[ColumnName]) + ' AND '
            #We drop the last AND from our statement
            Query = Query[0:-4]
        #Execute our query, save data to a cursor so we can get column names and data from an object
        Cursor = LibraryConnection.execute(Query)
        #Create an ordered list of our column names from the "description" value of our cursor
        ColumnNames = [description[0] for description in Cursor.description]
        #for each row that was returned
        for row in Cursor:
            #initialize a temporary dictionary
            TempDict = {}
            #map our data into our dictionary with the column name as the key
            for val, col in enumerate(Cursor.description):
                TempDict[col[0]] = row[val]
            #Append our temporary dictionary to our return value
            ReturnList.append(TempDict)
        #close our connection
        LibraryConnection.close()
    #if connection error
    #NOTE This shouldn't come up since the code will likely crash if there's an error connecting to the database
    else:
        print("ERROR: SQLite Database Connection error")
    #Return our return value
    return ReturnList


#Helper function to construct queries to update data in our SQLite database
def SQLUpdateEntry(TableName, Values, Restrictions):
    #Initialize our return value and connect to the database
    ReturnVal = 0
    LibraryConnection = sqlite3.connect("saves.db")
    #On connection success
    if LibraryConnection:
        #Initialize our Query generation
        Query = ''
        Query = 'UPDATE ' + TableName + ' SET '
        #Compile our query with the data from our passed in dictionary
        for column in Values:
            #must denote strings with 's per SQLs guidelines
            if type(Values[column]) == str:
                Query += column + " = '" + Values[column] + "', "
            #Must convert all non strings to strings for concatenation
            else:
                Query += column + " = " + str(Values[column]) + ", "
        #Drop the last comma from the Query
        Query = Query[0:-2]
        Query += '\n'
        #If we specify restrictions
        if Restrictions != {}:
            #we now know we need a where clause
            Query += ' WHERE '
            #compile the rest of our query from the restrictions
            for column in Restrictions:
                #Must denotes strings with 's
                if type(Restrictions[column]) == str:
                    Query += column + " = '" + Restrictions[column] + "' AND "
                #Must convert all non strings to strings for concatenation
                else:
                    Query += column + " = " + str(Restrictions[column]) + " AND "
            #Drop the last AND from the query
            Query = Query[0:-4]
        #Execute our query, commit the changes, and close our connection
        LibraryConnection.execute(Query)
        LibraryConnection.commit()
        LibraryConnection.close()
    #Error connecting to database
    #NOTE This shouldn't come up since the code likely crashes if there's an error connecting to the database
    else:
        ReturnVal = 1
        print("ERROR: SQLite Database Connection error")
    #Return our return value
    return ReturnVal

#Helper function to construct queries to delete rows from specified tables
def SQLDeleteEntry(TableName, Restrictions):
    #initialize our SQL connection and return value
    ReturnVal = 0
    LibraryConnection = sqlite3.connect("saves.db")
    #on connection success
    if LibraryConnection:
        #initialize our query
        Query = ''
        Query = 'DELETE FROM ' + TableName
        #if we make restrictions
        #NOTE there is a danger in calling this function with an empty restrictions parameter! It will delete all entries from the table if misused.
        if Restrictions != {}:
            #Initialize our where clause
            Query += ' WHERE '
            #Compile our where clause with our restriction values
            #NOTE all restrictions are assumed to be equal, not a separate comparison
            #May add in support for other comparisons, but it's a low priority
            for column in Restrictions:
                #Must denote strings with 's
                if type(Restrictions[column]) == str:
                    Query += column + " = '" + Restrictions[column] + "' AND "
                #Must convert non strings to strings
                else:
                    Query += column + " = " + str(Restrictions[column]) + " AND "
            #drop the last AND from our query
            Query = Query[0:-4]
        #execute our query, commit the changes, and close our connection
        LibraryConnection.execute(Query)
        LibraryConnection.commit()
        LibraryConnection.close()
    #Error connecting to database
    #NOTE this shouldn't come up since the code is likely to crash if there's an error connecting to the database
    else:
        ReturnVal = 1
        print("ERROR: SQLite Database Connection error")

    return ReturnVal

