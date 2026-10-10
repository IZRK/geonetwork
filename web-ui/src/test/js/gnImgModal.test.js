const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const registrations = {};
const angularModule = {
  directive(name, definition) {
    registrations[name] = definition;
    return this;
  },
  factory() {
    return this;
  },
  filter() {
    return this;
  },
  service() {
    return this;
  }
};

const context = {
  angular: { module: () => angularModule },
  goog: { provide() {} }
};
const source = fs.readFileSync(
  path.resolve(
    __dirname,
    "../../../src/main/resources/catalog/components/utility/UtilityDirective.js"
  ),
  "utf8"
);
vm.runInNewContext(source, context);

const definition = registrations.gnImgModal[
  registrations.gnImgModal.length - 1
](name => (value => value));
const imageUrl = "/geonetwork/api/records/eml-record/attachments/overview.png";

test("opens the clicked image when its EML overview is not indexed", () => {
  let clickHandler;
  let modalMarkup;
  let hideCount = 0;
  const modalDom = {};
  const viewportDom = {};
  const imageDom = { complete: false };
  const modalEvents = {};
  const viewportEvents = {};
  const imageCollection = {
    0: imageDom,
    first() {
      return this;
    },
    on() {
      return this;
    }
  };
  const viewport = {
    0: viewportDom,
    on(eventName, handler) {
      viewportEvents[eventName] = handler;
      return this;
    },
    width: () => 800,
    height: () => 600,
    scrollTop() {
      return this;
    },
    scrollLeft() {
      return this;
    }
  };
  const controls = {
    on() {
      return this;
    },
    text() {
      return this;
    }
  };
  const modal = {
    0: modalDom,
    modal(action) {
      if (action === "hide") {
        hideCount++;
      }
      return this;
    },
    on(eventName, handler) {
      modalEvents[eventName] = handler;
      return this;
    },
    find(selector) {
      if (selector === ".gn-img-modal-viewport") {
        return viewport;
      }
      if (selector === "img") {
        return imageCollection;
      }
      return controls;
    }
  };

  context.document = { body: {} };
  context.$ = () => ({ append() {} });
  context.angular.element = markup => {
    modalMarkup = markup;
    return modal;
  };

  definition.link(
    { $eval: () => ({ uuid: "eml-record" }) },
    {
      bind: (event, handler) => {
        assert.equal(event, "click");
        clickHandler = handler;
      },
      attr: name => (name === "src" ? imageUrl : undefined)
    },
    { gnImgModal: "md" }
  );

  assert.equal(typeof clickHandler, "function");
  clickHandler();
  assert.match(modalMarkup, new RegExp(`src="${imageUrl}"`));
  assert.match(modalMarkup, />−<\/button>/);
  assert.match(modalMarkup, />\+<\/button>/);
  assert.match(modalMarkup, /×<\/button>/);
  assert.doesNotMatch(modalMarkup, /<i class="fa /);

  modalEvents.click({ target: modalDom });
  viewportEvents.click({ target: viewportDom });
  assert.equal(hideCount, 2);
  viewportEvents.click({ target: imageDom });
  assert.equal(hideCount, 2);
});
