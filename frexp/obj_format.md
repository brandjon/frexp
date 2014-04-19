## Terminology ##

* **driven program:**
  the program that is being benchmarked

* **dataset:**
  a precise, repeatable sequence of operations to perform on the
  driven program; can be very large

* **dataset parameters:**
  a specification of the main characteristics of the dataset.
  Coupled with a generation procedure to produce a dataset.

* **trial:**
  an execution of the driven program

* **test parameters:**
  a dataset couple with other information needed for describing the trial

* **datapoint:**
  measured results of a trial


## Process overview ##

The overall workflow is

        dataset generation -> benchmarking -> analysis -> view

A separate verification step can also be used to check for semantically
correct output from the driven programs.

An experiment designer (i.e. a human) subclasses several base classes
to specify how to generate data, how to run tests, and what result data
to report. These subclasses are grouped together in an ExpWorkflow subclass.
The relevant methods and fields to override are:

* **Datagen.get_dsparams_list():**
  return a list of dataset parameters structures

* **Datagen.generate(dsp):**
  take a dataset parameters structure and return a dataset

* **Datagen.get_tparams_list(dsps):**
  take a list of dataset parameters structures and return a list
  of test parameters structures

* **Extractor.series:**
  a list of tuples describing the information to display

* **Extractor.get_series_data():**
  given a series id, return the subset of datapoints that belong
  to that series

* **Workflow.ExpDatagen**, **Workflow.ExpExtractor**,
  **Workflow.ExpDriver**, **Workflow.ExpVerifyDriver**:
  subclasses to use for this experiment

* Workflow also has other fields that control rerunning of experiments


## Data format ##

The following structures are passed throughout the workflow.
These structures are compatible with JSON but materialized on-disk
using pickle for efficiency.

Dataset parameters:

    {
        # Uniquely identifies this dataset, also used to
        # name the file the dataset's stored in.
        "dsid": <string>,
        # Test-specific data.
        ...
    }

Dataset:

    {
        # Dataset parameters object that this dataset
        # was created from.
        "dsparams": <Dataset params>,
        # Test-specific data.
        ...
    }

Test parameters:

    {
        # Id of dataset to feed to the driver
        "dsid": <string>,
        # Module to load as the driven program
        "prog": <string>,
        # Test-specific data.
        ...
    }

Datapoint:

    {
        # Dataset parameters used for the dataset
        # producing this point.
        "dsparams": <Dataset params>,
        # Test parameters used for this trial.
        "prog": <string>,
        ...
        # Result data.
        "results": ...
    }

Plot data:

    {
        "plot_title": <string>,
        "axes": [
            {
                "axes_title": <string>,
                "ylabel": <string>,
                "xlabel": <string>,
                "logx": <bool>,
                "logy": <bool>,
                "scalarx": <bool>,
                "scalary": <bool>,
                "series": [
                    {
                        "name": <string>,
                        "style": <string>,
                        "color": <string>,
                        "errorbars": <bool>,
                        "format": <one of "normal", "polyN", or "points">,
                        'hollow_markers': <bool>,
                        "data": [(<x>, <y>,
                                    <low_err_delta>, <hi_err_delta>), ...],
                    },
                ],
            },
            ...
            ],
        ],
        "config": {
            key: value
            // valid keys include:
            //   fontsize, legfontsize,
            //   xmin, xmax, ymin, ymax,
            //   linewidth, markersize,
            //   ticksize, tickwidth,
            //   figsize, max_xitvls, max_yitvls,
            //   x_ticklocs, y_ticklocs
        },
    }
