"""
Main application for NLP Resume Scanner and Job Recommender
"""

import datetime
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.express as px
import pandas as pd
from PIL import Image
import pytesseract
from wordcloud import WordCloud, STOPWORDS
import plotly.graph_objs as go

from io import BytesIO
import base64
import pickle
from collections import Counter

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer

def preprocess_nlp(text):
    lem = WordNetLemmatizer()
    tokenized_text=word_tokenize(text)
    tokenized_text = [lem.lemmatize(word.lower(),"v") for word in tokenized_text if (word not in STOPWORDS) & (len(word)>2)]
    return dict(Counter(tokenized_text).most_common(40))
  
df = pd.read_csv('../data/processed/concatenated_data_cleaned_labeled_preprocessed_alt.csv') 

def make_plots0(resume_text, df, filename):

    resume_counts = preprocess_nlp(resume_text)
    # for word in ['2018', '2019', '2020']:
    #     resume_counts.pop(word)
    all_counts = Counter(''.join(df['new_description'].to_list()).split() )

    subset_counts = { k:v for k, v in all_counts.items() if k in resume_counts.keys() }
    counts_df = pd.DataFrame(zip(resume_counts.keys() , resume_counts.values() ), columns = ['word', 'count'])
    counts_df['source'] = 'resume'
    concat_all = pd.DataFrame(zip(subset_counts.keys() , subset_counts.values() ), columns = ['word', 'count'])
    concat_all['source'] = 'training_data'

    final_df = pd.concat([counts_df, concat_all]).reset_index(drop=True)
    sum_all_data = -1*sum( final_df[final_df.source == 'training_data' ]['count'] ) 


    sum_res_data = sum( final_df[final_df.source == 'resume' ]['count'] ) 
    final_df.loc[final_df['source'] == 'training_data', 'count_norm'] = final_df['count']/sum_all_data
    final_df.loc[final_df['source'] == 'resume', 'count_norm'] = final_df['count']/sum_res_data

    fig = px.bar(
            final_df,
            x="word",
            y="count_norm",
            color="source",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"company": "Company:", "ngram": "N-Gram"},
            hover_data="",
        )

    fig.update_layout(title_text=f'Word Frequency Comparisons: "{filename}"', 
                    xaxis_tickangle=80,
                        yaxis=dict(
            title='Word Frequency (normalized)',
        ),
    )

    return fig

def plotly_wordcloud(string):
    """Helper function from Plotly
    https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-nlp/app.py"""

    word_cloud = WordCloud(stopwords=set(STOPWORDS), max_words=100, max_font_size=90)
    word_cloud.generate(string.lower())

    word_list = []
    freq_list = []
    fontsize_list = []
    position_list = []
    orientation_list = []
    color_list = []

    for (word, freq), fontsize, position, orientation, color in word_cloud.layout_:
        word_list.append(word)
        freq_list.append(freq)
        fontsize_list.append(fontsize)
        position_list.append(position)
        orientation_list.append(orientation)
        color_list.append(color)

    x_arr = []
    y_arr = []
    for i in position_list:
        x_arr.append(i[0])
        y_arr.append(i[1])

    new_freq_list = []
    for i in freq_list:
        new_freq_list.append(i * 80)

    trace = go.Scatter(
        x=x_arr,
        y=y_arr,
        textfont=dict(size=new_freq_list, color=color_list),
        hoverinfo="text",
        textposition="top center",
        hovertext=["{0} - {1}".format(w, f) for w, f in zip(word_list, freq_list)],
        mode="text",
        text=word_list,
    )

    layout = go.Layout(
        {
            "xaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "automargin": True,
                "range": [-100, 250],
            },
            "yaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "automargin": True,
                "range": [-100, 450],
            },
            "margin": dict(t=20, b=20, l=10, r=10, pad=4),
            "hovermode": "closest",
        }
    )

    wordcloud_figure_data = {"data": [trace], "layout": layout}
    word_list_top = word_list[:30]
    word_list_top.reverse()
    freq_list_top = freq_list[:30]
    freq_list_top.reverse()

    frequency_figure_data = {
        "data": [
            {
                "y": word_list_top,
                "x": freq_list_top,
                "type": "bar",
                "name": "",
                "orientation": "h",
            }
        ],
        "layout": {"height": "550", "margin": dict(t=20, b=20, l=100, r=20, pad=4)},
    }
    treemap_trace = go.Treemap(
        labels=word_list_top, parents=[""] * len(word_list_top), values=freq_list_top
    )
    treemap_layout = go.Layout({"margin": dict(t=10, b=10, l=5, r=5, pad=4)})
    treemap_figure = {"data": [treemap_trace], "layout": treemap_layout}
    return wordcloud_figure_data, frequency_figure_data, treemap_figure

def img_to_text(image_location):
    img = Image.open('../data/processed/' + image_location)
    text=pytesseract.image_to_string(img)
    return text

def make_plots1():
    return html.Div(
        style={ "padding": "10px"},
        children=[
        # image uploader
        html.Div(children = [
            html.H5("Drag and drop resume in here"),
            dcc.Upload(
                id='upload-image',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'}
                ),
            html.Div(id='output-image-upload')
            ],
        className="pretty_container three columns",),
        html.Div(
            children=[
                
                    dcc.Graph(
                    id='example-graph',
                    figure=fig
                        )
                ], 
            className="pretty_container nine columns"),
    ], className="row")


def make_plots2():
    return html.Div(
            children=[
                html.Div([
                    dbc.Card(WORDCLOUD_PLOTS),
                    ])
                ])

# initialize first resume eval
filename = 'example.png'
example_resume = img_to_text(filename)
wordcloud, frequency_figure, treemap = plotly_wordcloud(example_resume)

fig = make_plots0(example_resume, df, filename)

WORDCLOUD_PLOTS = [
    dbc.CardHeader(html.H6(f'Top words in "{filename}"')),
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-frequencies",
                            children=[dcc.Graph(figure=frequency_figure, id="frequency_figure")],
                            type="default",
                        )
                    ),
                    dbc.Col(
                        [
                            dcc.Tabs(
                                id="tabs",
                                children=[
                                    dcc.Tab(
                                        label="Treemap",
                                        children=[
                                            dcc.Loading(
                                                id="loading-treemap",
                                                children=[dcc.Graph(figure=treemap, id="bank-treemap")],
                                                type="default",
                                            )
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Wordcloud",
                                        children=[
                                            dcc.Loading(
                                                id="loading-wordcloud",
                                                children=[
                                                    dcc.Graph(figure=wordcloud, id="bank-wordcloud")
                                                ],
                                                type="default",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ],
                        md=8,
                    ),
                ]
            )
        ]
    ),
]

app.layout = html.Div(
    style={"background": "#fff8c7", "padding": "30px"},
    children=[
        html.Div(
            style={"background": "#ffffff", "padding": "20px",},
            children=[
                html.H1(children='NLP Classification Project'),

                html.H4(children='Resume Scanner and Job Recommender'),
                html.P(
                    style={"font-size": "18px"},
                    children='''A natural language processing recommendation app
                    curated for data-focused roles. Users can see what data job the NLP model 
                    recommends by uploading their resume below (NOTE: must be .png format).''')
                ]),
        make_plots1(),
        make_plots2()
    ]
)


def parse_contents(contents, filename, date):
    im = Image.open(BytesIO(base64.b64decode(contents.split(',')[1])))
    text = pytesseract.image_to_string(im)
    # im = Image.open(BytesIO(base64.b64decode(contents)))

    clf =  pickle.load( open( "../models/trigram_model.pkl", "rb" ) )
    cv =  pickle.load( open( "../models/count_vectorizer.pkl", "rb" ) )
    pred_result = clf.predict(cv.transform([text]))[0]

    return html.Div([
        html.H6(f'NLP Model suggests: {pred_result}'),
        html.Img(src=contents, style={'width':'100%'}),
    ]) , text

def plot_wordcloud_treemap(text):
    wordcloud, frequency_figure, treemap = plotly_wordcloud(text)
    return wordcloud, frequency_figure, treemap


@app.callback(
            Output('output-image-upload', 'children'),
              [Input('upload-image', 'contents')],
              [State('upload-image', 'filename'),
               State('upload-image', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children, text = parse_contents(list_of_contents, list_of_names, list_of_dates)
        return children

@app.callback(
            [Output("bank-wordcloud", "figure"),
            Output("frequency_figure", "figure"),
            Output("bank-treemap", "figure")],

            [Input('upload-image', 'contents')],
            [State('upload-image', 'filename'),
            State('upload-image', 'last_modified')])
def update_wordcloud_treemap_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children, text = parse_contents(list_of_contents, list_of_names, list_of_dates)
        wordcloud, frequency_figure, treemap = plot_wordcloud_treemap(text)
        return [wordcloud, frequency_figure, treemap]
    else:
        wordcloud, frequency_figure, treemap = plotly_wordcloud(example_resume)
        return [wordcloud, frequency_figure, treemap]
if __name__ == '__main__':
    app.run_server(debug=True)

