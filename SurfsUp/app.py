 #http://localhost:5000/

# Import the dependencies.
import numpy as np
import pandas as pd
from scipy import stats
import datetime

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
#Resources\hawaii.sqlite
#engine = create_engine("sqlite:////Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )


#Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.

#Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)


    # Starting from the most recent data point in the database. 
    most_recent_date = get_most_recent_measurement_date(session)

    # Calculate the date one year from the last date in data set.
    last_year_date = pd.to_datetime(most_recent_date) + pd.DateOffset(years= -1)
    last_year_date = last_year_date.strftime("%Y-%m-%d")

    # Perform a query to retrieve the data and precipitation scores
    # Query precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= last_year_date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_observations
    all_observations = []
    for date, prcp in results:
        observation_dict = {}
        observation_dict["date"] = date
        observation_dict["prcp"] = prcp
        
        all_observations.append(observation_dict)

    return jsonify(all_observations)




@app.route("/api/v1.0/stations")
def names():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all passengers
    results = session.query(Station.name).all()

    session.close()

    # Convert list of tuples into normal list
    all_names = list(np.ravel(results))

    return jsonify(all_names)


@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)


    # Starting from the most recent data point in the database. 
    most_recent_date = get_most_recent_measurement_date(session)

    # Calculate the date one year from the last date in data set.
    last_year_date = pd.to_datetime(most_recent_date) + pd.DateOffset(years= -1)
    last_year_date = last_year_date.strftime("%Y-%m-%d")

    # Perform a query to retrieve the data and precipitation scores
    # Query precipitation data
    results = get_tobs_rows(session, last_year_date, most_recent_date)
    session.close()

    # Create a dictionary from the row data and append to a list of all_observations
    all_observations = []
    for date, tobs in results:
        observation_dict = {}
        observation_dict["date"] = date
        observation_dict["tobs"] = tobs
        
        all_observations.append(observation_dict)

    return jsonify(all_observations)



@app.route("/api/v1.0/<start>")
def temp_data_start_date(start):
    
    session = Session(engine)
    #set end date to most recent date
    end = get_most_recent_measurement_date(session)

    # Query precipitation data
    tobs_results = get_tobs_rows(session, start, end)
    df = pd.DataFrame(tobs_results)
    tobs_stats = get_tobs_stats(session, df["tobs"])

    session.close()
    return jsonify(tobs_stats)


@app.route("/api/v1.0/<start>/<end>")
def temp_data_start_stop_dates(start, end):
    session = Session(engine)
    # Query precipitation data
    tobs_results = get_tobs_rows(session, start, end)
    df = pd.DataFrame(tobs_results)
    tobs_stats = get_tobs_stats(session, df["tobs"])

    session.close()
    
    return jsonify(tobs_stats)


#for testing function
@app.route("/api/v1.0/test_recent_date")
def find_most_recent_date():
    session = Session(engine)
    recent_date = get_most_recent_measurement_date(session)
    session.close()
    return recent_date



#Get most recent measurement date
def get_most_recent_measurement_date(inSession):
    return inSession.query(Measurement.date).order_by(Measurement.date.desc()).first().date



#Get results/rows of tobs within a given date
def get_tobs_rows(inSession, in_start_date, in_end_date):
    
    results = inSession.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= in_start_date).\
        filter(Measurement.date <= in_end_date).all()
    
    return results


#Calculate tobs stats and return list of dict to jsonify
def get_tobs_stats(inSession, inListOfTob):
    stats_list = []
    stats_list.append({"min temp:" : stats.tmin(inListOfTob)})
    stats_list.append({"avg temp:" : stats.tmean(inListOfTob)})
    stats_list.append({"max temp:" : stats.tmax(inListOfTob)})

    return stats_list

if __name__ == '__main__':
    app.run(debug=True)