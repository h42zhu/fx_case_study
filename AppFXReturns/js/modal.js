import React from 'react';

class DataModal extends React.Component {

  render() {
    const {isShowing, data, onClose} = this.props;

    const disp = isShowing? { display: 'block' } : { display: 'none' };
    return(
    <div className="modal" style={disp}>
      <div className="modal-background"></div>
      <div className="modal-card">
        <header className="modal-card-head">
        <p className="modal-card-title">FX Data</p>
        <button className="delete" onClick={onClose}></button>
        </header>
        <section className="modal-card-body">
        <table className="table">
        <thead>
          <tr>
          <th>Value Date</th>
          <th>Currency</th>
          <th>Base Currency</th>
          <th>FX Rate</th>
          </tr>
        </thead>
        <tbody>
          {data.map(item=>{
            return(
              <tr>
                {item.map(cell=>{
                  return(<td>{cell}</td>)}
                )}
              </tr>)})}
        </tbody>
        </table>
        </section>
        <footer className="modal-card-foot">
        <button className="button" onClick={onClose}>Close</button>
        </footer>
      </div>
    </div>
    )
  }
}

export default DataModal;