import React from 'react';
import ReactDOM from 'react-dom';
import { getCSRFToken } from './util'
import DataModal from './modal'

const csrftoken = getCSRFToken()

const DEFAULT_OPTION = {
  credentials: 'same-origin',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrftoken,
  },
}

class App extends React.Component {
  constructor(props) {
    super(props);
    this.onGenerateReport = this.onGenerateReport.bind(this);
    this.onShowData = this.onShowData.bind(this);
  }

  componentWillMount() {
    this.setState({
      startYear: '',
      endYear: '',
      years: [],
      currency: 'all',
      report: 'daily_return',

      // modal related
      isShowing: false,
      data: [],
    });

    const url = '/fx_returns/get_date_range/';
    fetch(url, DEFAULT_OPTION)
      .then(res => res.json())
      .then(jsonObj => this.setState({
        years: jsonObj.years,
        startYear: Math.min(...jsonObj.years),
        endYear: Math.max(...jsonObj.years),
      }))
      .catch(err => console.log(err))
  }

  onShowData() {
    const { startYear, endYear, currency, report } = this.state;
    if (Number(startYear) > Number(endYear)) {
      alert('Start Year cannot be greater than End Year!')
      return;
    }

    // api call to fetch and display data
    const url = '/fx_returns/show_data/';
    const query = {
      start_year: startYear,
      end_year: endYear,
      currency,
      report,
    };

    fetch(url, Object.assign({}, DEFAULT_OPTION,
      {
        method: 'post',
        body: JSON.stringify(query),
      }))
      .then(res => res.json())
      .then(jsonObj => this.setState({
        isShowing: true,
        data: jsonObj.data || [],
      }))
  }

  onGenerateReport() {
    const { startYear, endYear, currency, report } = this.state;
    if (Number(startYear) > Number(endYear)) {
      alert('Start Year cannot be greater than End Year!')
      return;
    }
    // api call to generate the report
    const url = '/fx_returns/gen_report/';
    const query = {
      start_year: startYear,
      end_year: endYear,
      currency,
      report,
    };

    fetch(url, Object.assign({}, DEFAULT_OPTION,
      {
        method: 'post',
        body: JSON.stringify(query),
      }))
      .then((res) => {
        if (res.status !== 200) {
          alert('Error: problem generating the report!')
        }
        return res.blob();
      })
      .then((blob) => {
        const newBlob = new Blob([blob], {type: "application/pdf"})
        const data = window.URL.createObjectURL(newBlob);
        window.open(data, 'pdf_report');
      })
  }


  render() {
    return (
      <div style={{ marginTop: 10 }}>
        <div>Start Year</div>
        <div className="select">
        <select
          value={this.state.startYear} 
          onChange={e => this.setState({ startYear: e.target.value })}>
            { this.state.years.map((item) => {
              return (<option value={item}>{item}</option>)
            })}
          </select>
        </div>

        <div>End Year</div>
        <div className="select">
        <select
          value={this.state.endYear} 
          onChange={e => this.setState({ endYear: e.target.value })}>
            { this.state.years.map((item) => {
              return (<option value={item}>{item}</option>)
            })}
          </select>
        </div>

        <div>GBP vs Currency</div>
        <div className="select">
          <select
            value={this.state.currency} 
            onChange={e => this.setState({ currency: e.target.value })}>
            {['all', 'usd', 'eur'].map((item) => {
              return (<option value={item}>{item.toUpperCase()}</option>)
            })}
          </select>
        </div>

        <div>Report Type</div>
        <div className="select">
          <select
            value={this.state.report} 
            onChange={e => this.setState({ report: e.target.value })}
            style={{ textTransform: 'capitalize' }}>
            {['daily_return', 'rolling_average',
              'rolling_standard_deviation', 'rolling_covariance',
              'rolling_correlation'].map((item) => {
              return (
                <option value={item} style={{ textTransform: 'capitalize' }}>
                  {item.replace(/_/g, ' ')}
                </option>)
            })}
          </select>
        </div>

        <br /><br />
        <a className="button is-primary is-outlined" onClick={this.onShowData}>
          Show Data
        </a>
        <a className="button is-primary is-outlined" onClick={this.onGenerateReport}>
          Generate Report
        </a>

        <DataModal 
          isShowing={this.state.isShowing}
          data={this.state.data}
          onClose={()=>{this.setState({isShowing: false})}}
        />
      </div>
    );
  }
}


ReactDOM.render(
  <App />,
  document.getElementById('root'),
);
