import pandas as pd
import panel as pn
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Output, Input
import dash_bootstrap_components as dbc

countries=['United States','Russia','China','Japan','Germany','India','United Kingdom', 'France','Indonesia']
sources=['co2_coal','co2_oil','co2_gas','co2_cement']
components=['co2','share_global_co2','co2_per_gdp','co2_per_capita','methane']
comp_labels=['CO2 (Million Tonnes)','Fraction Share Global','CO2 per GDP','Tonnes per Person','Methane (Million Tonnes)']
comp_max=[10000, 50, 1.2, 20, 1200]

lastyears = list(map(str,[*range(2020,1950,-1)]))

mloa_file='https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/daily/daily_in_situ_co2_mlo.csv'
mloa_df = pd.read_csv(mloa_file,skiprows=45)

mloa_df.columns=['Yr','Mn','Dy','CO2','NHrs','Scale']
# convert co2 to float
mloa_df['co2']=mloa_df['CO2'].astype(float)
mloa_df.dropna(inplace=True)
mloa_df['Date']=pd.to_datetime(dict(year=mloa_df.Yr,month=mloa_df.Mn,day=mloa_df.Dy))

# energy mix --- needs pre-processing
dfmix = pd.read_csv('per-capita-energy-stacked.csv')
dfmix = dfmix[dfmix.Entity.isin(countries)]
dfmix.columns=['country','code','year','coal','oil','gas','nuclear','hydro','wind','solar','other']
dfmix=dfmix.dropna()
#dfmix['total']=dfmix['coal','oil','gas','nuclear','hydro','wind','solar','other'].sum(axis=1)

# get component fractions ie normalize
dfmix['total']=dfmix.iloc[:,3:12].sum(axis=1)
dfmix['Coal']=dfmix['coal']/dfmix['total']
dfmix['Oil']=dfmix['oil']/dfmix['total']
dfmix['Gas']=dfmix['gas']/dfmix['total']
dfmix['Nuclear']=dfmix['nuclear']/dfmix['total']
dfmix['Hydro']=dfmix['hydro']/dfmix['total']
dfmix['Wind']=dfmix['wind']/dfmix['total']
dfmix['Solar']=dfmix['solar']/dfmix['total']
dfmix['Other']=dfmix['other']/dfmix['total']

print (dfmix.sample(5))



df = pd.read_csv('https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv')
# cache data to improve dashboard performance
if 'data' not in pn.state.cache.keys():

    df = pd.read_csv('https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv')

    pn.state.cache['data'] = df.copy()

else: 

    df = pn.state.cache['data']



# data cleanup
df=df.fillna(0)
df_major=df[(df['country'].isin(countries)) & (df['year']>1940)]
df_countries_full=df[df.iso_code!='0']
df_countries=df_countries_full[df_countries_full.year==2018]
#print(df_major.sample(30))
df_major_year=df_major[df_major.year==2018]

yearmks = [*range(1950,2020,10)]

fig_mloa=px.line(mloa_df, x='Date',y='co2',title='Mauna Loa CO2 Measurements').update_layout(yaxis_title='CO2 PPM')
fig_choro=px.choropleth(df_countries,locations='iso_code',color='co2_per_capita',
    color_continuous_scale=px.colors.sequential.Plasma, range_color=(0,10000))

#app=Dash(__name__)
app=Dash(external_stylesheets=[dbc.themes.CERULEAN])
app.layout=html.Div(className='top-level',children=[
    html.Div(className='header',children=[
        html.H1('CO2 Production')
    ]),
    html.Div(className='fullrow',children=[
        dcc.Graph(id='mloa_plot',figure=fig_mloa),
        dcc.Graph(id='choro_map', figure=fig_choro)
    ]),
    html.Div(className='bigrow',children=[
        html.Div(className='sidebar',children=[
            html.H2(children='Constituent'),
            dcc.RadioItems(['co2','share_global_co2','co2_per_gdp','co2_per_capita','methane'],value='co2',id='yaxis_select'),
            html.Br(),
            html.H6(children='Year Range'),
            dcc.RangeSlider(1950,2020,1,value=[1950,2020],id='year_rangeslider',marks={
                1950:'1950',
                #1960:'1960',
                1970:'1970',
                #1980:'1980',
                1990:'1990',
                #2000:'2000',
                2010:'2010'
            }) 
        ]),
        
        html.Div(className='main-content',children=[
            
            dcc.Graph(id='tsa_plot',figure=px.line(df_major,x='year',y='co2',title='CO2 Production',color='country')),
            #dcc.Graph(id='choro_map', figure=fig_choro)
        ]),

        html.Div(className='main-content',children=[
            dcc.Graph(id='sources_plot',
                figure=px.bar(df_major_year,x='country',y=['coal_co2','gas_co2','oil_co2'],title='CO2 Makeup'))
        ])
    
    ]),
    html.Div(className='bigrow',children=[
        html.Div(className='sidebar',children=[
            html.H3('Country Analysis'),
            dcc.Dropdown(id='year_select',options=lastyears,value=2018),
            dcc.Dropdown(id='country_select',options=countries,value='United States')
        ]
        ),
        html.Div(className='main-content',children=[
            
            dcc.Graph(id='indiv_plot')
    
        ]),
        html.Div(className='main-content',children=[
            
            dcc.Graph(id='mix_plot')
    
        ])
    ])
    

])




@app.callback(
    [
    Output('choro_map',"figure"),
    Output('tsa_plot',"figure"),
    Output('sources_plot',"figure"),
    Output('indiv_plot',"figure"),
    Output('mix_plot',"figure"),
    ],
    [Input('yaxis_select',"value"),
    Input('year_rangeslider',"value"),
    Input('country_select','value'),
    Input('year_select','value')
    ]
)
def update_plot(inval,year_range, indiv_country, useyear):

    use_index= components.index(inval)
    ymax = comp_max[use_index]
    ylabel = comp_labels[use_index]

    df_country = df_countries_full[(df_countries_full.country==indiv_country)&(df_countries_full.year>=year_range[0])&
                             (df_countries_full.year<=year_range[1])]
    df_mix = dfmix[(dfmix.country==indiv_country) & (dfmix.year>=year_range[0]) & (dfmix.year<=year_range[1])]
    
    newdf = df_major[(df_major.year>=year_range[0]) & (df_major.year <=year_range[1]) ]
    useyear=(int(useyear))
    df_major_year=df_major[(df_major.year==useyear)]
    print(df_major_year.head())
    fig_bar=px.bar(df_major_year,x='country',y=['coal_co2','gas_co2','oil_co2'],
            title='CO2 Makeup - Major Countries').update_layout(yaxis_title='CO2 (Million Tonnes)')
    
    #max = df_countries_full].max()
    fig_choro=px.choropleth(df_countries,locations='iso_code',color=inval,
                             color_continuous_scale=px.colors.sequential.Plasma, range_color=(0,ymax))
    
    print(df_country.head(25))
    fig_indiv_plot = px.line(df_country, x='year',y=['co2','coal_co2','gas_co2','coal_co2','oil_co2'],
            title='CO2 Mix').update_layout(yaxis_title=ylabel)

    figure=px.line(newdf,x='year',y=inval,title='CO2 Production - Major Countries',
            color='country').update_layout(yaxis_title=ylabel)


    fig_mix=px.line(df_mix,x='year',y=['Coal','Oil','Gas','Nuclear','Hydro','Solar','Wind','Other'],
            title='Energy Mix').update_layout(yaxis_title='Fraction')
    return (fig_choro, figure, fig_bar, fig_indiv_plot,fig_mix)
            




if __name__=="__main__":
    app.run_server(debug=True)