import firebase_admin
from firebase_admin import auth

import mesop as me
import mesop.labs as mel

from google.cloud import bigquery
import pandas as pd

from dotenv import load_dotenv
import os
from dataclasses import field

from firebase_auth_component import (
  firebase_auth_component,
)

# Avoid re-initializing firebase app (useful for avoiding warning message because of hot reloads).
if firebase_admin._DEFAULT_APP_NAME not in firebase_admin._apps:
  default_app = firebase_admin.initialize_app()


load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
BIGQUERY_TABLE = os.getenv('BIGQUERY_TABLE')
IMAGE_BASE_URL = os.getenv('IMAGE_BASE_URL')

lookup = {
    "Country":{"k":"select_label", "v":"label"},
    "What language is this label written in?": {"k":"task_label", "v":"value"},
    "County":{"k":"select_label", "v":"value"},
    "DAO Accession Number\n": {"k":"task_label", "v":"value"},
    'Scientific Name': {'k': 'task_label', 'v': 'value'},
    'Collected By': {'k': 'task_label', 'v': 'value'},
    'Verbatim Date': {'k': 'task_label', 'v': 'value'},
    'Are there geographic coordinates present?': {'k': 'task_label', 'v': 'value'},
    "Collection Date (year)": {'k': 'select_label', 'v': 'label'},
    "Collection Date (month)": {'k': 'select_label', 'v': 'label'},
    'Collection Date (day)': { 'k': 'select_label', 'v': 'label'},
}



@me.stateclass
class State:
  data: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
  email: str


def get_data_from_bigquery():

  state = me.state(State)
  if not state.data.empty:
    return state.data

  bigquery_client = bigquery.Client(project=PROJECT_ID)
  query = f"""
    SELECT classification_id, filename, scientific_name
    FROM `{BIGQUERY_TABLE}`
  """
  query_job = bigquery_client.query(query)
  results = query_job.result()

  data = results.to_dataframe()
  state.data = data

  return data

def get_row(id):
  bigquery_client = bigquery.Client(project=PROJECT_ID)
  query = f"""
    SELECT *
    FROM `{BIGQUERY_TABLE}`
    WHERE classification_id = {id}
    LIMIT 1
  """
  query_job = bigquery_client.query(query)
  results = query_job.result()

  return next(results)


def load(e: me.LoadEvent):
  me.set_theme_mode("system")

@me.page(
  on_load=load,
  path="/",
  title="Classification with GenAI",
  stylesheets=[
    "https://www.gstatic.com/firebasejs/ui/6.1.0/firebase-ui-auth.css"
  ],
  # Loosen the security policy so the firebase JS libraries work.
  security_policy=me.SecurityPolicy(
    dangerously_disable_trusted_types=True,
    allowed_connect_srcs=["*.googleapis.com"],
    allowed_script_srcs=[
      "*.google.com",
      "https://www.gstatic.com",
      "https://cdn.jsdelivr.net",
    ],
  ),
)
def app():

  with me.box(style=me.Style(
      margin=me.Margin.all(0),
      padding=me.Padding.all(0),
      display="grid",
      grid_template_rows="auto auto 1fr",
      height="100%"
  )):

    with me.box(style=me.Style(
        background="#f0f0f0",
        padding=me.Padding.all(20),
        display="grid",
        grid_template_columns="1fr auto",
    )):
      with me.box(style=me.Style(margin=me.Margin.all(0))):
        me.text("Classification Evaluation with GenAI", type='headline-1', 
          style=me.Style(
              font_size="1.5em", 
              line_height="1.5em", 
              margin=me.Margin.all(0), padding=me.Padding.all(0)))
      with me.box(style=me.Style(margin=me.Margin.all(0))):
        firebase_auth_component(on_auth_changed=on_auth_changed)
          
    if me.state(State).email:
      with me.box(style=me.Style(margin=me.Margin.all(20))):
        me.markdown("## The Data")
        state = me.state(State)

        data = get_data_from_bigquery()

        me.table(
          data,
          header=me.TableHeader(sticky=True),
          on_click=on_click,
          columns={},
        )

@me.page(
  path="/subject", 
  on_load=load,  title="Classification with GenAI",
  stylesheets=[
    "https://www.gstatic.com/firebasejs/ui/6.1.0/firebase-ui-auth.css"
  ],
  # Loosen the security policy so the firebase JS libraries work.
  security_policy=me.SecurityPolicy(
    dangerously_disable_trusted_types=True,
    allowed_connect_srcs=["*.googleapis.com"],
    allowed_script_srcs=[
      "*.google.com",
      "https://www.gstatic.com",
      "https://cdn.jsdelivr.net",
    ],
  ))
def page_2():

  classification_id = me.query_params["c"]
  data = get_row(classification_id)
  me.set_page_title(f"Classification with GenAI - {str(data.scientific_name)}")

  with me.box(style=me.Style(
      margin=me.Margin.all(0),
      padding=me.Padding.all(0),
      display="grid",
      grid_template_rows="auto auto 1fr",
      height="100%"
  )):

    with me.box(style=me.Style(
        background="#f0f0f0",
        padding=me.Padding.all(20),
        display="grid",
        grid_template_columns="1fr auto",
    )):
      with me.box(style=me.Style(margin=me.Margin.all(0))):
        me.text("Classification Evaluation with GenAI", type='headline-1', 
          style=me.Style(
              font_size="1.5em", 
              line_height="1.5em", 
              margin=me.Margin.all(0), padding=me.Padding.all(0)))
      with me.box(style=me.Style(margin=me.Margin.all(0))):
        firebase_auth_component(on_auth_changed=on_auth_changed)

    with me.box(style=me.Style(
        background="#fff",
        padding=me.Padding.all(20),
        display="flex", flex_direction="row", justify_content="space-between"
    )):
      me.link(text="Back to list", url="/")

      [next_classification_id, next_title] = get_next_classification_id(classification_id)

      next_url = f"/subject?c={next_classification_id}"
      me.link(text=f"Next ({next_title})", url=next_url)

    if me.state(State).email:
      with me.box(style=me.Style(
          margin=me.Margin.all(10),
          display="grid",
          grid_template_rows="auto 1fr",
          grid_template_columns="40rem 1fr",
          height="100%"
      )):
        with me.box(style=me.Style(margin=me.Margin.all(10))):
          me.markdown(f"## Scientific name: {str(data.scientific_name)}")
          me.markdown(f"### Filename: {str(data.filename)}")
          me.markdown(f"### Classification id: {str(data.classification_id)}")

          me.markdown(f"## Human annotations")
          annotation_keys = data.parsed_annotations.keys()
          for key in annotation_keys:
            me.markdown(f"* {key}: {data.parsed_annotations[key]}")

          me.markdown(f"## AI Generation")
          me.markdown(f"* {'Collected by'}: {data.ai_generation['Collected by']}")
          me.markdown(f"* {'Identification Numbers'}: {data.ai_generation['Identification Numbers']}")
          me.markdown(f"* {'Scientific Name'}: {data.ai_generation['Scientific Name']}")
          me.markdown(f"* {'Description'}: {data.ai_generation['content']}")
          me.markdown(f"* {'Label language'}: {data.ai_generation['label language']}")
          me.markdown(f"* {'Date / Verbatim Date'}: {data.ai_generation['date']['Verbatim Date']}")
          me.markdown(f"* {'Date / Year'}: {data.ai_generation['date']['Year']}")
          me.markdown(f"* {'Location / Location Verbatim'}: {data.ai_generation['location']['Location Verbatim']}")      
          me.markdown(f"* {'Location / Country'}: {data.ai_generation['location']['country']}")
          me.markdown(f"* {'Location / County'}: {data.ai_generation['location']['county']}")
          # me.markdown(f"* {'Location / Lat Long'}: {data.ai_generation['location']['Lat Long']}")
          # me.markdown(f"* {'Location / Are there geographic coordinates present?'}: {data.ai_generation['location']['Are there geographic coordinates present?']}")

          me.markdown(f"## Human evaluation")
          me.markdown(f"* {'Score'}: {data.human_evaluation['score']}")
          me.markdown(f"* {'Description'}: {data.human_evaluation['evaluation']}")

          me.markdown(f"### {'Differences'}")
          for item in data.human_evaluation['differences']:
            me.markdown(f"* {item}")

          me.markdown(f"### {'Missing fields'}")
          for item in data.human_evaluation['missing fields']:
            me.markdown(f"* {item}")


        
        with me.box(style=me.Style(margin=me.Margin.all(10))):
          me.image(
            src=f"{IMAGE_BASE_URL}{data['filename']}",
            alt=str(data.scientific_name),
            style=me.Style(width="100%"),
          )  

def on_click(e: me.TableClickEvent):
  data = get_data_from_bigquery()
  classification_id = data.iat[e.row_index, 0]
  me.query_params["c"] = str(classification_id)
  me.navigate("/subject", query_params=me.query_params)

def get_next_classification_id(classification_id):
  
  data = get_data_from_bigquery()

  row_index = None
  for index, row in data.iterrows():
    if row['classification_id'] == float(classification_id):
        row_index = index

  next_row_index = row_index + 1
  if next_row_index < len(data):  # Check for last row
      next_classification_id = data.iat[next_row_index, 0]
      next_classification_title = data.iat[next_row_index, 2]
      return [next_classification_id, next_classification_title]
  else:
      return None


def on_auth_changed(e: mel.WebEvent):
  print("on change")
  firebaseAuthToken = e.value
  if not firebaseAuthToken:
    me.state(State).email = ""
    return

  decoded_token = auth.verify_id_token(firebaseAuthToken)
  # You can do an allowlist if needed.
  # if decoded_token["email"] != "allowlisted.user@gmail.com":
  #   raise me.MesopUserException("Invalid user: " + decoded_token["email"])
  me.state(State).email = decoded_token["email"]

