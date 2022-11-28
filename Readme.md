# Barracuda Dashboard

**Authors:** Alex Burnham, Quinlan Dubois

This dashboard is built using [Plotly Dash](https://plotly.com/dash/) and [Pandas](https://pandas.pydata.org/).

Additional Libraries include:
- [Numpy](https://numpy.org/)
- [Statsmodels](https://www.statsmodels.org/stable/index.html)

### Naming Conventions
- **File_Names**: first letter capital of each word, words separated by underscores.
- **parameterNames**: first word lowercase, following words first letter capital, no word separation.
- **CONSTANT_NAMES**: all uppercase, words separated by underscores.
- **variable_names**: all lowercase, words separated by underscores.
- **"argument_strings"**: all lowercase, words separated by underscores. As strings.
- **"component-ids"**: all lowercase words separated by hyphens. As strings.


### Currently Accepted Datatypes:
- CSV

### Directions for adding datasets to the Dashboard:
- Run `Data_Json_Generator.py` and follow its instructions.
- Add a section for the dataset in the marked Dataset Loader section in the header of the `Barracuda_Dashboard.py` file.
  - The code should look like this:
    ```python
    # Required, replace all <> with the relevant information.
    # <> with the same label must be replaced by the same text.
    data_<dataset> = "data/<filename>.csv"
    df_<dataset> = pd.read_csv(data_<dataset>)
    
    # Optional, use this line if you need to change the datatype of a column, typically I've found 
    df_<dataset>['<column>'] = df_<dataset>['<column>'].astype("<type>")
    ```
- Add a condition for the dataset in the `select_dataframe()` method at the end of the `Barracuda_Dashboard.py` file.
  - The code should look like this:
    ```python
    # Required, replace all <> with the relevant information.
    # <> with the same label must be replaced by the same text.
    elif dataframe_label == '<filename>.csv':
        return df_<dataset>
    ```
    
