import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import base64
from dash import callback
import requests
  
#figure = go.Figure(go.Scatter(name="Model", x=top50_results['year'], y=top50_results['rank']))

external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Poppins:wght@600&display=swap",
    "/assets/model_styles.css",
    "/assets/styles.css"
]

dash.register_page(__name__)

header = html.Div(
    id="app-header-model",
    children=[
        html.H1("Use the model yourself!"),
    ]
)

upload = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div(id="upload-data-div", children = [
            'Drag and Drop or ',
            html.A('Select File')
        ]),
        # Allow multiple files to be uploaded
        multiple=False
    ),
])

def get_genre(decoded):#
    files = {"file": decoded}
    res = requests.post('http://ec2-3-6-41-170.ap-south-1.compute.amazonaws.com:8050/', files=files)
    return eval(res.text)

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)

    try:
        if 'mp3' in filename or 'wav' in filename:
            genres = get_genre(decoded)
            decoded = None
            results = [
                html.H2("Top 5 Predicted Genres")
            ]
            for genre in genres:
                results.append(html.P(genre)),#, style=genre_styles[genre]))
            results = html.Div(children=results[:6], id='results_div')
            output = html.Div(["File accepted!", html.Br()], id="output-div")
        else:
            output = html.Div(["Please upload an MP3 or WAV File"], id="output-div")
            results = html.Br()
            
    except Exception as e:
        #print(e)
        return html.Div(id='error-div', children=[ html.Br(), 
            'There was an error processing this file. Please try reuploading or upload a different file if that doesn\'t work. Sorry for the inconvenience!'
        ])

    return html.Div(id="result-div", children=[
        html.H3(f"File Received:"),
        html.H3(f"{filename}"),
        output,
        html.Br(),  # horizontal line
        results
    ])
    
@callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(content, name, date):
    if content is not None:
        children = [
            parse_contents(content, name, date)]
        return children


layout = html.Div(
    id="model-main",
    children=[
        header,
        upload,
        html.Div(id='output-data-upload')
    ]
)

