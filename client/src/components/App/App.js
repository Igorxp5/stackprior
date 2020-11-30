import React from 'react';

import Items from '../../containers/Items';
import Header from '../Header/Header';
import NSModal from '../NewServiceModal/NewServiceModal';

import 'bootstrap/dist/css/bootstrap.min.css';

import { Button, Container, Col, Row } from 'react-bootstrap';
import './App.scss';

const App = () => {


  const [modalShow, setModalShow] = React.useState(false);

  return(
    <div id="home-page">
        <Header />
        <Container>
          <Row className="items-top">
            <Col>
              <div className="title">
                <h1> SERVICES </h1>
              </div>
            </Col>
            <Col className="items-listed">
              <Button className="btn-app" variant="primary" onClick={() => setModalShow(true)}>New Service</Button>
              {modalShow ? (
                <NSModal
                  callbackParent={(bool) => setModalShow(bool)}
                  show={modalShow}
                  onHide={() => setModalShow(false)}
                />
              ) :null
            }
            </Col>
          </Row>
          <Row>
            <div>
              <Items />
            </div>
          </Row>
        </Container>
    </div>
  )
}

export default App;