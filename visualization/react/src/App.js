import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

import Ideogram from 'ideogram';

class App extends Component {
  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1 className="App-title">Welcome to Ideogram in React!</h1>
        </header>
        <AppIdeogram/>
      </div>
    );
  }
}

class AppIdeogram extends Component {

  componentDidMount() {

    // TODO: Fix filter.js in Ideogram to remove need for this global variable
    window.ideogram = new Ideogram({
      organism: 'human',
      assembly: 'GRCh37',
      orientation: 'horizontal',
      chrHeight: 80,
      chrMargin: 10,
      showBandLabels: false,
      // legend: legend,
      annotationHeight: 30,
      annotationsLayout: 'heatmap',
      dataDir: 'https://unpkg.com/ideogram@0.13.0/dist/data/bands/native/',
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