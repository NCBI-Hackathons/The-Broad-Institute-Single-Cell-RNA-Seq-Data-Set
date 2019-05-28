import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

import Ideogram from 'ideogram';

var authButtonStyle = {
  marginLeft: '25px'
};
var revokeButtonStyle = {
  display: 'none',
  marginLeft: '25px'
}



class App extends Component {
  render() {

    return (
      <div className="App">
        <header className="App-header">
          <h1>Single-cell analysis of cancer | Bio-IT hackathon 2019</h1>
          <p>
          Single-cell RNA-seq can be used to infer copy number variations.  Below, <a href="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5465819">four brain cancer samples</a> show large deletions in chr1p and chr19q, among other cytogenetic abnormalities.
          </p>
          <p id="summary_external_host">
          This prototype reproduces a study in <a href="https://portals.broadinstitute.org/single_cell/study/SCP384">Single Cell Portal</a> using <a href="https://github.com/broadinstitute/inferCNV/wiki">inferCNV</a> workflow output as run on <a href="https://app.terra.bio">Terra</a>.  Visualizations use <a href="https://github.com/eweitz/ideogram">Ideogram.js</a>.
          </p>
          <button id="sign-in-or-out-button" style={authButtonStyle}>Sign in / Authorize</button>
          <button id="revoke-access-button" style={revokeButtonStyle}>Revoke access</button>
        </header>
        <AppIdeogram/>
      </div>
    );
  }
}

class AppIdeogram extends Component {

  componentDidMount() {

    var legend = [{
      name: 'Expression level',
      rows: [
        {name: 'Low', color: '#33F'},
        {name: 'Normal', color: '#CCC'},
        {name: 'High', color: '#F33'}
      ]
    }];

    // TODO: Fix filter.js in Ideogram to remove need for this global variable
    window.ideogram = new Ideogram({
      organism: 'human',
      assembly: 'GRCh37',
      orientation: 'horizontal',
      chrHeight: 80,
      chrMargin: 10,
      showBandLabels: false,
      legend: legend,
      annotationHeight: 30,
      annotationsLayout: 'heatmap',
      dataDir: 'https://unpkg.com/ideogram@1.8.0/dist/data/bands/native/',
      // annotationsPath: 'https://www.googleapis.com/storage/v1/b/single-cell/o/oligodendroglioma%2fideogram_exp_means__Observations--Sample--group--cluster.json?alt=media',
      annotationsPath: 'data/ideogram_exp_means__observation--Sample--group--cluster.json',
      geometry: 'collinear'
    });


    return window.ideogram;
  }

  render() {
    return (
      <div id="ideo-container"></div>
    );
  }
}

export default App;