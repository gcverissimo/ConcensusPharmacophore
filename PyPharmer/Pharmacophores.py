__version__ = "0.1.0"
__author__  = "https://github.com/AngelRuizMoreno"

''' 
################### PHARMIT EXECUTABLE ###################
'''
from importlib_resources import files

__PHARMIT      = files("PyPharmer.bin").joinpath("pharmitserver")
__PHARMIT_LIC  = files("PyPharmer.bin").joinpath("README")


''' 
################### TOOLBOX ###################
'''

__all__=
['get_ligand_receptor_pharmacophore','get_molecule_pharmacophore','parse_json_pharmacophore','show_pharmacophoric_descriptors','save_pharmacophore_to_pymol','compute_concensus_pharmacophore']


import os, subprocess, json

import pandas as pd


import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from pymol import cmd

from scipy.spatial import distance_matrix
import scipy.cluster.hierarchy as sch
from sklearn.preprocessing import normalize
import numpy as np
import seaborn as sns


def get_ligand_receptor_pharmacophore (receptor:str,ligand:str,out:str,out_format:str='json',cmd:str='pharma'):
    
    """
    Generate a pharmacophore model for a ligand-receptor complex.

    This function uses the PHARMIT tool to create a pharmacophore model based on the interaction between a ligand and a receptor. The output can be in JSON or XML format.

    Args:
        receptor (str): The file name of the receptor structure in PDB format.
        ligand (str): The file name of the ligand structure in SDF or MOL2 format.
        out (str): The base name of the output file.
        out_format (str, optional): The format of the output file. Defaults to 'json'.
        cmd (str, optional): The command to run PHARMIT. Defaults to 'pharma'.

    Returns:
        None

    Example:
        >>> get_ligand_receptor_pharmacophore('receptor.pdb', 'ligand.sdf', 'pharmacophore')
        b'{"pharmacophore": [{"type": "hydrophobic", "center": [1.2, 3.4, 5.6], "radius": 1.5}, ...]}'
    """
    args = (__PHARMIT,"-cmd", cmd, "-receptor", receptor, "-in", ligand, "-out", f'{out}.{out_format}')
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    
def get_molecule_pharmacophore (ligand:str,out:str,out_format:str='json',cmd:str='pharma'):
    """
    Generate a pharmacophore model for a molecule.

    This function uses the PHARMIT tool to create a pharmacophore model based on the features and properties of a molecule. The output can be in JSON or XML format.

    Args:
        ligand (str): The file name of the molecule structure in SDF or MOL2 format.
        out (str): The base name of the output file.
        out_format (str, optional): The format of the output file. Defaults to 'json'.
        cmd (str, optional): The command to run PHARMIT. Defaults to 'pharma'.

    Returns:
        None

    Example:
        >>> get_molecule_pharmacophore('ligand.sdf', 'pharmacophore')
        b'{"pharmacophore": [{"type": "hydrophobic", "center": [1.2, 3.4, 5.6], "radius": 1.5}, ...]}'
    """
    args = (__PHARMIT,"-cmd", cmd, "-in", ligand, "-out", f'{out}.{out_format}')
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    

def parse_json_pharmacophore (json_file:str):
    """Parse a JSON file containing a pharmacophore model.

    This function reads a JSON file that contains a pharmacophore model generated by PHARMIT and returns a pandas DataFrame with the pharmacophore points and their colors, as well as the ligand and receptor structural data in MOL and MOL strings (if applicable).

    Args:
        json_file (str): The file name of the JSON file containing the pharmacophore model.

    Returns:
        tuple: A tuple of three elements:
            - table (pd.DataFrame): A DataFrame with the columns 'name', 'center', 'radius', and 'color' for each pharmacophore point.
            - lig (str): The file name of the ligand structure used to generate the pharmacophore model.
            - receptor (str): The file name of the receptor structure used to generate the pharmacophore model.

    Example:
        >>> table, lig, receptor = parse_json_pharmacophore('pharmacophore.json')
        >>> table
                  name              center  radius   color
        0   Hydrophobic  [1.2, 3.4, 5.6]     1.5    green
        ... ... ... ... ...
        >>> lig
        'ligand data'
        >>> receptor
        'receptor data'
    """
    
    
    color_code={ 'Hydrophobic':        'green',\
                 'HydrogenAcceptor':   'orange',\
                 'HydrogenDonor':      'white',\
                 'Aromatic':           'purple',\
                 'NegativeIon':        'red',\
                 'PositiveIon':        'navy',\
                 'InclusionSphere':    'gray',\
                 'Other':              'yellow',\
                 'PhenylalanineAnalog':'pink',\
                 'LeuValAnalog':       'pink' \
                 }
    
    with open (json_file, 'r') as file:
        data = json.load(file)
        table=pd.DataFrame(data.get('points'))
    
    table['color']=table['name'].map(color_code)

    lig=data.get('ligand')
    receptor=data.get('receptor')

    return table, lig, receptor


def show_pharmacophoric_descriptors(table:pd.DataFrame,selection:str='enabled',show_vectors:bool=True):
    """Show a 3D scatter plot of the pharmacophore points with optional vectors.

    This function uses the plotly and pandas libraries to create a 3D scatter plot of the pharmacophore points with different colors and sizes based on their names and radii. The function also allows to show or hide the vectors associated with some of the points.

    Args:
        table (pd.DataFrame): A DataFrame with the columns 'name', 'center', 'radius', 'color', 'enabled', and 'svector' for each pharmacophore point.
        selection (str, optional): A string indicating which points to show in the plot. It can be 'enabled', 'disabled', or 'all'. Defaults to 'enabled'.
        show_vectors (bool, optional): A boolean indicating whether to show the vectors or not. Defaults to True.

    Returns:
        None: The function does not return anything, but displays the plot in a new window.

    Example:
        >>> table, lig, receptor = parse_json_pharmacophore('pharmacophore.json')
        >>> show_pharmacophoric_descriptors(table, selection='all', show_vectors=False)
        # A 3D scatter plot of all the pharmacophore points without vectors is shown.
    """
    
    if selection=='enabled':
        table=table[table.enabled==True]
    if selection == 'disabled':
        table=table[table.enabled==False]
    if selection =='all':
        table=table
        
    
    fig=go.Figure()
    sca = px.scatter_3d(table, x='x', y='y', z='z', size='radius',color='name',color_discrete_map=table.set_index("name")[["color"]].to_dict()['color'],hover_name='ligand')

    sca.update_traces(marker=dict(size=12,
                                  line=dict(width=2,
                                            color='DarkSlateGrey')),
                      selector=dict(mode='markers'))


    for plot in sca.data:
        fig.add_trace(plot)

    if show_vectors==True:
        u=[sv['x'] for sv in table.svector if isinstance(sv,dict)]
        v=[sv['y'] for sv in table.svector if isinstance(sv,dict)]
        w=[sv['z'] for sv in table.svector if isinstance(sv,dict)]
        
        cl='black'
        
        vectors = go.Figure(data = go.Cone(
            x=table.dropna(subset=['svector'])['x'],
            y=table.dropna(subset=['svector'])['y'],
            z=table.dropna(subset=['svector'])['z'],
            u=u,
            v=v,
            w=w,
            lighting_roughness=1,
            showlegend=False,
            showscale=False,
            sizemode='absolute',
            colorscale=[cl,cl],
            sizeref=0.2))

        fig.add_trace(vectors.data[0])

    else:
        pass

    fig.update_layout(width=800,height=800,scene=dict(aspectratio=dict(x=1, y=1, z=0.8),
                                 camera_eye=dict(x=1.2, y=1.2, z=0.6)))

    return fig.show()



def save_pharmacophore_to_pymol (table:pd.DataFrame,out_file:str='pharmacophore.pse',select:str='all'):
    """Save a pharmacophore model to a PyMOL session file.

    This function uses the PyMOL command line interface to create pseudoatoms for each pharmacophore point and save them to a PyMOL session file. The function also allows to group the points by cluster, concensus, or name.

    Args:
        table (pd.DataFrame): A DataFrame with the columns 'name', 'center', 'radius', 'color', 'cluster', 'weight', 'balance', and 'svector' for each pharmacophore point.
        out_file (str, optional): The file name of the PyMOL session file to be written. Defaults to 'pharmacophore.pse'.
        select (str, optional): A string indicating how to group the points in PyMOL. It can be 'cluster', 'concensus', or 'all'. Defaults to 'all'.

    Returns:
        None: The function does not return anything, but writes the PyMOL session file.

    Example:
        >>> table, lig, receptor = parse_json_pharmacophore('pharmacophore.json')
        >>> save_pharmacophore_to_pymol(table, out_file='pharmacophore.pse', select='cluster')
        # A PyMOL session file with the pharmacophore points grouped by cluster is written.
    """
    
    if select=='cluster':
        for point in table.index:
            cmd.pseudoatom(object=int(table.loc[point,'cluster']),resn=table.loc[point,'name'],
                               resi=point, chain='P', elem='PS',label=int(table.loc[point,'cluster']),
                               vdw=table.loc[point,'radius'], hetatm=1, color=table.loc[point,'color'],b=table.loc[point,'weight'],
                           q=table.loc[point,'balance'],pos=[table.loc[point,'x'],table.loc[point,'y'],table.loc[point,'z']])

            cmd.group(table.loc[point,'name'], '*')
    
    elif select=='concensus':
        for point in table.index:
            cmd.pseudoatom(object=table.loc[point,'name'],resn=table.loc[point,'name'],
                           resi=point, chain='P', elem='PS',label=table.loc[point,'name'],
                           vdw=table.loc[point,'radius'], hetatm=1, color=table.loc[point,'color'],b=table.loc[point,'weight'],
                           q=table.loc[point,'balance'],pos=[table.loc[point,'x'],table.loc[point,'y'],table.loc[point,'z']])
            
            cmd.group('Concensus', '*')
        
    elif select=='all':
        for point in table.index:
            cmd.pseudoatom(object=table.loc[point,'name'],resn=table.loc[point,'name'],
                           resi=point, chain='P', elem='PS',label=table.loc[point,'name'],
                           vdw=table.loc[point,'radius'], hetatm=1, color=table.loc[point,'color'],
                           pos=[table.loc[point,'x'],table.loc[point,'y'],table.loc[point,'z']])
    
    else:
        print("parameter select must be 'all', 'cluster' or 'concensus'")
    
    cmd.show(representation='spheres')
    cmd.center(selection='all')
    cmd.save(out_file,format='pse')
    cmd.remove('all')
    cmd.reinitialize(what='everything')
    

def save_pharmacophore_to_json (table:pd.DataFrame,out_file:str='pharmacophore.json'):
    """Save a pharmacophore model to a JSON file.

    This function converts a pandas DataFrame containing the pharmacophore points to a JSON format and writes it to a file. The JSON format is compatible with the PHARMIT tool for pharmacophore-based virtual screening.

    Args:
        table (pd.DataFrame): A DataFrame with the columns 'name', 'center', 'radius', and optionally 'color', 'cluster', 'weight', 'balance', and 'svector' for each pharmacophore point.
        out_file (str, optional): The file name of the JSON file to be written. Defaults to 'pharmacophore.json'.

    Returns:
        None: The function does not return anything, but writes the JSON file.

    Example:
        >>> table, lig, receptor = parse_json_pharmacophore('pharmacophore.json')
        >>> save_pharmacophore_to_json(table, out_file='pharmacophore_new.json')
        # A JSON file with the pharmacophore points is written.
    """
    
    data=f'"points":{table.to_json(orient="records")}'
    data="{"+data+"}"

    with open(out_file,'w') as f:
        f.write(data)
        
def compute_concensus_pharmacophore (table:pd.DataFrame, save_data_per_descriptor:bool=True, out_folder:str='.', h_dist:float=0.17):
    """
    Computes the concensus pharmacophore from a table of 3D coordinates and features of molecular descriptors.

    Parameters
    ----------
    table : pd.DataFrame, optional
        A pandas dataframe containing the name, x, y, z, color and cluster columns of the molecular descriptors. 
    save_data_per_descriptor : bool, optional
        A flag indicating whether to save the data and plots for each descriptor cluster or not. The default is True.
    out_folder : str, optional
        The output folder where the data and plots will be saved. The default is '.'.
    h_dist : float, optional
        The distance threshold for hierarchical clustering. The default is 0.17.

    Returns
    -------
    Concensus : pd.DataFrame
        A pandas dataframe containing the name, cluster, x, y, z, radius, color, weight and balance columns of the concensus pharmacophore.
    Links : dict
        A dictionary containing the distance matrix and linkage matrix for each descriptor cluster.
    
    Example
    -------
    >>> table = pd.read_csv('example.csv')
    >>> Concensus, Links = compute_concensus_pharmacophore(table)
    >>> Concensus
              name  cluster         x         y         z  radius  color  weight   balance
    1  Hydrophobic        1 -0.063333 -0.063333 -0.063333     1.0      1       3  0.333333
    2   Donor_Acceptor        1 -0.063333 -0.063333 -0.063333     0.5      2       3  0.333333
    """
    
    def __compute_cluster(table:pd.DataFrame):
        
        if len(table.index)>2:
            
            matrix=distance_matrix(x=table[['x','y','z']],y=table[['x','y','z']])
            dm = sch.distance.pdist(matrix)
            linkage = sch.linkage(dm, method='complete')
            clusters = sch.fcluster(linkage, 0.17*dm.max(), 'distance')

            table['cluster']=clusters


            weight=[]
            for row in matrix:
                weight.append(len([distance for distance in row if distance <= 1.5]))

            table['weight']=weight

            table['balance']=normalize([weight], norm="l1")[0]
                
        return linkage,matrix,table
        
    def __compute_center_of_mass_and_radius(table:pd.DataFrame):

        center_of_mass = np.average([table['x'],table['y'],table['z']], axis=1, weights=table['weight'])
        radius = max([np.linalg.norm(center_of_mass - np.array((table.loc[i,'x'],table.loc[i,'y'],table.loc[i,'z']))) for i in table.index])/2

        if radius<1 and 'Hydrophobic' in list(table.name):
            radius=1
        elif radius<0.5 and 'Hydrophobic' not in list(table.name):
            radius=0.5

        return center_of_mass,radius 
    
        
    Concensus=pd.DataFrame()
    Links={}
    Descriptors=table.groupby('name')
    index=1
    for group in Descriptors.groups:
        linkage,matrix,descriptor_cluster=__compute_cluster(Descriptors.get_group(group))
        Links[group]={'matrix':matrix,'linkage':linkage}
        
        if save_data_per_descriptor==True:
            save_pharmacophore_to_pymol(table=descriptor_cluster,out_file=f"{out_folder}/{group}_clusters.pse",select='cluster')
            
            fig=sns.clustermap (matrix,method='complete',figsize=(10,10),xticklabels=descriptor_cluster.index, yticklabels=descriptor_cluster.index,
                                cmap='RdBu',cbar_kws=dict(label='Distance',shrink=1,orientation='vertical',spacing='uniform',pad=0.02),
                                    row_linkage=linkage, col_linkage=linkage, rasterized=True)
            
            fig.savefig(f"{out_folder}/{group}_clusters.png",dpi=300)
        
        else:
            pass
        
        clusters=descriptor_cluster.groupby('cluster')
        for cg in clusters.groups:
            clus=clusters.get_group(cg)
            center_of_mass,radius=__compute_center_of_mass_and_radius(clus)
            Concensus.loc[index,'name']=group
            Concensus.loc[index,'cluster']=cg
            Concensus.loc[index,'x']=center_of_mass[0]
            Concensus.loc[index,'y']=center_of_mass[1]
            Concensus.loc[index,'z']=center_of_mass[2]
            Concensus.loc[index,'radius']=radius
            Concensus.loc[index,'color']=clus.loc[clus.index[0],'color']
            Concensus.loc[index,'weight']=int(len(clus.index))
            Concensus.loc[index,'balance']=clus['balance'].mean()
            index=index+1
    
    return Concensus, Links