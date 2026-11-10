var Iu={exports:{}},zo={},Uu={exports:{}},Tt={};/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var im;function e_(){if(im)return Tt;im=1;var s=Symbol.for("react.element"),e=Symbol.for("react.portal"),t=Symbol.for("react.fragment"),r=Symbol.for("react.strict_mode"),o=Symbol.for("react.profiler"),l=Symbol.for("react.provider"),u=Symbol.for("react.context"),f=Symbol.for("react.forward_ref"),d=Symbol.for("react.suspense"),p=Symbol.for("react.memo"),v=Symbol.for("react.lazy"),g=Symbol.iterator;function _(P){return P===null||typeof P!="object"?null:(P=g&&P[g]||P["@@iterator"],typeof P=="function"?P:null)}var S={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},M=Object.assign,A={};function y(P,B,Z){this.props=P,this.context=B,this.refs=A,this.updater=Z||S}y.prototype.isReactComponent={},y.prototype.setState=function(P,B){if(typeof P!="object"&&typeof P!="function"&&P!=null)throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,P,B,"setState")},y.prototype.forceUpdate=function(P){this.updater.enqueueForceUpdate(this,P,"forceUpdate")};function x(){}x.prototype=y.prototype;function O(P,B,Z){this.props=P,this.context=B,this.refs=A,this.updater=Z||S}var D=O.prototype=new x;D.constructor=O,M(D,y.prototype),D.isPureReactComponent=!0;var R=Array.isArray,z=Object.prototype.hasOwnProperty,H={current:null},I={key:!0,ref:!0,__self:!0,__source:!0};function N(P,B,Z){var ue,he={},K=null,oe=null;if(B!=null)for(ue in B.ref!==void 0&&(oe=B.ref),B.key!==void 0&&(K=""+B.key),B)z.call(B,ue)&&!I.hasOwnProperty(ue)&&(he[ue]=B[ue]);var Ee=arguments.length-2;if(Ee===1)he.children=Z;else if(1<Ee){for(var ye=Array(Ee),we=0;we<Ee;we++)ye[we]=arguments[we+2];he.children=ye}if(P&&P.defaultProps)for(ue in Ee=P.defaultProps,Ee)he[ue]===void 0&&(he[ue]=Ee[ue]);return{$$typeof:s,type:P,key:K,ref:oe,props:he,_owner:H.current}}function C(P,B){return{$$typeof:s,type:P.type,key:B,ref:P.ref,props:P.props,_owner:P._owner}}function T(P){return typeof P=="object"&&P!==null&&P.$$typeof===s}function F(P){var B={"=":"=0",":":"=2"};return"$"+P.replace(/[=:]/g,function(Z){return B[Z]})}var $=/\/+/g;function ee(P,B){return typeof P=="object"&&P!==null&&P.key!=null?F(""+P.key):B.toString(36)}function le(P,B,Z,ue,he){var K=typeof P;(K==="undefined"||K==="boolean")&&(P=null);var oe=!1;if(P===null)oe=!0;else switch(K){case"string":case"number":oe=!0;break;case"object":switch(P.$$typeof){case s:case e:oe=!0}}if(oe)return oe=P,he=he(oe),P=ue===""?"."+ee(oe,0):ue,R(he)?(Z="",P!=null&&(Z=P.replace($,"$&/")+"/"),le(he,B,Z,"",function(we){return we})):he!=null&&(T(he)&&(he=C(he,Z+(!he.key||oe&&oe.key===he.key?"":(""+he.key).replace($,"$&/")+"/")+P)),B.push(he)),1;if(oe=0,ue=ue===""?".":ue+":",R(P))for(var Ee=0;Ee<P.length;Ee++){K=P[Ee];var ye=ue+ee(K,Ee);oe+=le(K,B,Z,ye,he)}else if(ye=_(P),typeof ye=="function")for(P=ye.call(P),Ee=0;!(K=P.next()).done;)K=K.value,ye=ue+ee(K,Ee++),oe+=le(K,B,Z,ye,he);else if(K==="object")throw B=String(P),Error("Objects are not valid as a React child (found: "+(B==="[object Object]"?"object with keys {"+Object.keys(P).join(", ")+"}":B)+"). If you meant to render a collection of children, use an array instead.");return oe}function ne(P,B,Z){if(P==null)return P;var ue=[],he=0;return le(P,ue,"","",function(K){return B.call(Z,K,he++)}),ue}function ce(P){if(P._status===-1){var B=P._result;B=B(),B.then(function(Z){(P._status===0||P._status===-1)&&(P._status=1,P._result=Z)},function(Z){(P._status===0||P._status===-1)&&(P._status=2,P._result=Z)}),P._status===-1&&(P._status=0,P._result=B)}if(P._status===1)return P._result.default;throw P._result}var re={current:null},V={transition:null},me={ReactCurrentDispatcher:re,ReactCurrentBatchConfig:V,ReactCurrentOwner:H};function ie(){throw Error("act(...) is not supported in production builds of React.")}return Tt.Children={map:ne,forEach:function(P,B,Z){ne(P,function(){B.apply(this,arguments)},Z)},count:function(P){var B=0;return ne(P,function(){B++}),B},toArray:function(P){return ne(P,function(B){return B})||[]},only:function(P){if(!T(P))throw Error("React.Children.only expected to receive a single React element child.");return P}},Tt.Component=y,Tt.Fragment=t,Tt.Profiler=o,Tt.PureComponent=O,Tt.StrictMode=r,Tt.Suspense=d,Tt.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=me,Tt.act=ie,Tt.cloneElement=function(P,B,Z){if(P==null)throw Error("React.cloneElement(...): The argument must be a React element, but you passed "+P+".");var ue=M({},P.props),he=P.key,K=P.ref,oe=P._owner;if(B!=null){if(B.ref!==void 0&&(K=B.ref,oe=H.current),B.key!==void 0&&(he=""+B.key),P.type&&P.type.defaultProps)var Ee=P.type.defaultProps;for(ye in B)z.call(B,ye)&&!I.hasOwnProperty(ye)&&(ue[ye]=B[ye]===void 0&&Ee!==void 0?Ee[ye]:B[ye])}var ye=arguments.length-2;if(ye===1)ue.children=Z;else if(1<ye){Ee=Array(ye);for(var we=0;we<ye;we++)Ee[we]=arguments[we+2];ue.children=Ee}return{$$typeof:s,type:P.type,key:he,ref:K,props:ue,_owner:oe}},Tt.createContext=function(P){return P={$$typeof:u,_currentValue:P,_currentValue2:P,_threadCount:0,Provider:null,Consumer:null,_defaultValue:null,_globalName:null},P.Provider={$$typeof:l,_context:P},P.Consumer=P},Tt.createElement=N,Tt.createFactory=function(P){var B=N.bind(null,P);return B.type=P,B},Tt.createRef=function(){return{current:null}},Tt.forwardRef=function(P){return{$$typeof:f,render:P}},Tt.isValidElement=T,Tt.lazy=function(P){return{$$typeof:v,_payload:{_status:-1,_result:P},_init:ce}},Tt.memo=function(P,B){return{$$typeof:p,type:P,compare:B===void 0?null:B}},Tt.startTransition=function(P){var B=V.transition;V.transition={};try{P()}finally{V.transition=B}},Tt.unstable_act=ie,Tt.useCallback=function(P,B){return re.current.useCallback(P,B)},Tt.useContext=function(P){return re.current.useContext(P)},Tt.useDebugValue=function(){},Tt.useDeferredValue=function(P){return re.current.useDeferredValue(P)},Tt.useEffect=function(P,B){return re.current.useEffect(P,B)},Tt.useId=function(){return re.current.useId()},Tt.useImperativeHandle=function(P,B,Z){return re.current.useImperativeHandle(P,B,Z)},Tt.useInsertionEffect=function(P,B){return re.current.useInsertionEffect(P,B)},Tt.useLayoutEffect=function(P,B){return re.current.useLayoutEffect(P,B)},Tt.useMemo=function(P,B){return re.current.useMemo(P,B)},Tt.useReducer=function(P,B,Z){return re.current.useReducer(P,B,Z)},Tt.useRef=function(P){return re.current.useRef(P)},Tt.useState=function(P){return re.current.useState(P)},Tt.useSyncExternalStore=function(P,B,Z){return re.current.useSyncExternalStore(P,B,Z)},Tt.useTransition=function(){return re.current.useTransition()},Tt.version="18.3.1",Tt}var rm;function gd(){return rm||(rm=1,Uu.exports=e_()),Uu.exports}/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var sm;function t_(){if(sm)return zo;sm=1;var s=gd(),e=Symbol.for("react.element"),t=Symbol.for("react.fragment"),r=Object.prototype.hasOwnProperty,o=s.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,l={key:!0,ref:!0,__self:!0,__source:!0};function u(f,d,p){var v,g={},_=null,S=null;p!==void 0&&(_=""+p),d.key!==void 0&&(_=""+d.key),d.ref!==void 0&&(S=d.ref);for(v in d)r.call(d,v)&&!l.hasOwnProperty(v)&&(g[v]=d[v]);if(f&&f.defaultProps)for(v in d=f.defaultProps,d)g[v]===void 0&&(g[v]=d[v]);return{$$typeof:e,type:f,key:_,ref:S,props:g,_owner:o.current}}return zo.Fragment=t,zo.jsx=u,zo.jsxs=u,zo}var om;function n_(){return om||(om=1,Iu.exports=t_()),Iu.exports}var W=n_(),Oe=gd(),fl={},Fu={exports:{}},zn={},Ou={exports:{}},ku={};/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var am;function i_(){return am||(am=1,(function(s){function e(V,me){var ie=V.length;V.push(me);e:for(;0<ie;){var P=ie-1>>>1,B=V[P];if(0<o(B,me))V[P]=me,V[ie]=B,ie=P;else break e}}function t(V){return V.length===0?null:V[0]}function r(V){if(V.length===0)return null;var me=V[0],ie=V.pop();if(ie!==me){V[0]=ie;e:for(var P=0,B=V.length,Z=B>>>1;P<Z;){var ue=2*(P+1)-1,he=V[ue],K=ue+1,oe=V[K];if(0>o(he,ie))K<B&&0>o(oe,he)?(V[P]=oe,V[K]=ie,P=K):(V[P]=he,V[ue]=ie,P=ue);else if(K<B&&0>o(oe,ie))V[P]=oe,V[K]=ie,P=K;else break e}}return me}function o(V,me){var ie=V.sortIndex-me.sortIndex;return ie!==0?ie:V.id-me.id}if(typeof performance=="object"&&typeof performance.now=="function"){var l=performance;s.unstable_now=function(){return l.now()}}else{var u=Date,f=u.now();s.unstable_now=function(){return u.now()-f}}var d=[],p=[],v=1,g=null,_=3,S=!1,M=!1,A=!1,y=typeof setTimeout=="function"?setTimeout:null,x=typeof clearTimeout=="function"?clearTimeout:null,O=typeof setImmediate<"u"?setImmediate:null;typeof navigator<"u"&&navigator.scheduling!==void 0&&navigator.scheduling.isInputPending!==void 0&&navigator.scheduling.isInputPending.bind(navigator.scheduling);function D(V){for(var me=t(p);me!==null;){if(me.callback===null)r(p);else if(me.startTime<=V)r(p),me.sortIndex=me.expirationTime,e(d,me);else break;me=t(p)}}function R(V){if(A=!1,D(V),!M)if(t(d)!==null)M=!0,ce(z);else{var me=t(p);me!==null&&re(R,me.startTime-V)}}function z(V,me){M=!1,A&&(A=!1,x(N),N=-1),S=!0;var ie=_;try{for(D(me),g=t(d);g!==null&&(!(g.expirationTime>me)||V&&!F());){var P=g.callback;if(typeof P=="function"){g.callback=null,_=g.priorityLevel;var B=P(g.expirationTime<=me);me=s.unstable_now(),typeof B=="function"?g.callback=B:g===t(d)&&r(d),D(me)}else r(d);g=t(d)}if(g!==null)var Z=!0;else{var ue=t(p);ue!==null&&re(R,ue.startTime-me),Z=!1}return Z}finally{g=null,_=ie,S=!1}}var H=!1,I=null,N=-1,C=5,T=-1;function F(){return!(s.unstable_now()-T<C)}function $(){if(I!==null){var V=s.unstable_now();T=V;var me=!0;try{me=I(!0,V)}finally{me?ee():(H=!1,I=null)}}else H=!1}var ee;if(typeof O=="function")ee=function(){O($)};else if(typeof MessageChannel<"u"){var le=new MessageChannel,ne=le.port2;le.port1.onmessage=$,ee=function(){ne.postMessage(null)}}else ee=function(){y($,0)};function ce(V){I=V,H||(H=!0,ee())}function re(V,me){N=y(function(){V(s.unstable_now())},me)}s.unstable_IdlePriority=5,s.unstable_ImmediatePriority=1,s.unstable_LowPriority=4,s.unstable_NormalPriority=3,s.unstable_Profiling=null,s.unstable_UserBlockingPriority=2,s.unstable_cancelCallback=function(V){V.callback=null},s.unstable_continueExecution=function(){M||S||(M=!0,ce(z))},s.unstable_forceFrameRate=function(V){0>V||125<V?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):C=0<V?Math.floor(1e3/V):5},s.unstable_getCurrentPriorityLevel=function(){return _},s.unstable_getFirstCallbackNode=function(){return t(d)},s.unstable_next=function(V){switch(_){case 1:case 2:case 3:var me=3;break;default:me=_}var ie=_;_=me;try{return V()}finally{_=ie}},s.unstable_pauseExecution=function(){},s.unstable_requestPaint=function(){},s.unstable_runWithPriority=function(V,me){switch(V){case 1:case 2:case 3:case 4:case 5:break;default:V=3}var ie=_;_=V;try{return me()}finally{_=ie}},s.unstable_scheduleCallback=function(V,me,ie){var P=s.unstable_now();switch(typeof ie=="object"&&ie!==null?(ie=ie.delay,ie=typeof ie=="number"&&0<ie?P+ie:P):ie=P,V){case 1:var B=-1;break;case 2:B=250;break;case 5:B=1073741823;break;case 4:B=1e4;break;default:B=5e3}return B=ie+B,V={id:v++,callback:me,priorityLevel:V,startTime:ie,expirationTime:B,sortIndex:-1},ie>P?(V.sortIndex=ie,e(p,V),t(d)===null&&V===t(p)&&(A?(x(N),N=-1):A=!0,re(R,ie-P))):(V.sortIndex=B,e(d,V),M||S||(M=!0,ce(z))),V},s.unstable_shouldYield=F,s.unstable_wrapCallback=function(V){var me=_;return function(){var ie=_;_=me;try{return V.apply(this,arguments)}finally{_=ie}}}})(ku)),ku}var lm;function r_(){return lm||(lm=1,Ou.exports=i_()),Ou.exports}/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var cm;function s_(){if(cm)return zn;cm=1;var s=gd(),e=r_();function t(n){for(var i="https://reactjs.org/docs/error-decoder.html?invariant="+n,a=1;a<arguments.length;a++)i+="&args[]="+encodeURIComponent(arguments[a]);return"Minified React error #"+n+"; visit "+i+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}var r=new Set,o={};function l(n,i){u(n,i),u(n+"Capture",i)}function u(n,i){for(o[n]=i,n=0;n<i.length;n++)r.add(i[n])}var f=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),d=Object.prototype.hasOwnProperty,p=/^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/,v={},g={};function _(n){return d.call(g,n)?!0:d.call(v,n)?!1:p.test(n)?g[n]=!0:(v[n]=!0,!1)}function S(n,i,a,c){if(a!==null&&a.type===0)return!1;switch(typeof i){case"function":case"symbol":return!0;case"boolean":return c?!1:a!==null?!a.acceptsBooleans:(n=n.toLowerCase().slice(0,5),n!=="data-"&&n!=="aria-");default:return!1}}function M(n,i,a,c){if(i===null||typeof i>"u"||S(n,i,a,c))return!0;if(c)return!1;if(a!==null)switch(a.type){case 3:return!i;case 4:return i===!1;case 5:return isNaN(i);case 6:return isNaN(i)||1>i}return!1}function A(n,i,a,c,h,m,E){this.acceptsBooleans=i===2||i===3||i===4,this.attributeName=c,this.attributeNamespace=h,this.mustUseProperty=a,this.propertyName=n,this.type=i,this.sanitizeURL=m,this.removeEmptyString=E}var y={};"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(n){y[n]=new A(n,0,!1,n,null,!1,!1)}),[["acceptCharset","accept-charset"],["className","class"],["htmlFor","for"],["httpEquiv","http-equiv"]].forEach(function(n){var i=n[0];y[i]=new A(i,1,!1,n[1],null,!1,!1)}),["contentEditable","draggable","spellCheck","value"].forEach(function(n){y[n]=new A(n,2,!1,n.toLowerCase(),null,!1,!1)}),["autoReverse","externalResourcesRequired","focusable","preserveAlpha"].forEach(function(n){y[n]=new A(n,2,!1,n,null,!1,!1)}),"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(n){y[n]=new A(n,3,!1,n.toLowerCase(),null,!1,!1)}),["checked","multiple","muted","selected"].forEach(function(n){y[n]=new A(n,3,!0,n,null,!1,!1)}),["capture","download"].forEach(function(n){y[n]=new A(n,4,!1,n,null,!1,!1)}),["cols","rows","size","span"].forEach(function(n){y[n]=new A(n,6,!1,n,null,!1,!1)}),["rowSpan","start"].forEach(function(n){y[n]=new A(n,5,!1,n.toLowerCase(),null,!1,!1)});var x=/[\-:]([a-z])/g;function O(n){return n[1].toUpperCase()}"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(n){var i=n.replace(x,O);y[i]=new A(i,1,!1,n,null,!1,!1)}),"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(n){var i=n.replace(x,O);y[i]=new A(i,1,!1,n,"http://www.w3.org/1999/xlink",!1,!1)}),["xml:base","xml:lang","xml:space"].forEach(function(n){var i=n.replace(x,O);y[i]=new A(i,1,!1,n,"http://www.w3.org/XML/1998/namespace",!1,!1)}),["tabIndex","crossOrigin"].forEach(function(n){y[n]=new A(n,1,!1,n.toLowerCase(),null,!1,!1)}),y.xlinkHref=new A("xlinkHref",1,!1,"xlink:href","http://www.w3.org/1999/xlink",!0,!1),["src","href","action","formAction"].forEach(function(n){y[n]=new A(n,1,!1,n.toLowerCase(),null,!0,!0)});function D(n,i,a,c){var h=y.hasOwnProperty(i)?y[i]:null;(h!==null?h.type!==0:c||!(2<i.length)||i[0]!=="o"&&i[0]!=="O"||i[1]!=="n"&&i[1]!=="N")&&(M(i,a,h,c)&&(a=null),c||h===null?_(i)&&(a===null?n.removeAttribute(i):n.setAttribute(i,""+a)):h.mustUseProperty?n[h.propertyName]=a===null?h.type===3?!1:"":a:(i=h.attributeName,c=h.attributeNamespace,a===null?n.removeAttribute(i):(h=h.type,a=h===3||h===4&&a===!0?"":""+a,c?n.setAttributeNS(c,i,a):n.setAttribute(i,a))))}var R=s.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED,z=Symbol.for("react.element"),H=Symbol.for("react.portal"),I=Symbol.for("react.fragment"),N=Symbol.for("react.strict_mode"),C=Symbol.for("react.profiler"),T=Symbol.for("react.provider"),F=Symbol.for("react.context"),$=Symbol.for("react.forward_ref"),ee=Symbol.for("react.suspense"),le=Symbol.for("react.suspense_list"),ne=Symbol.for("react.memo"),ce=Symbol.for("react.lazy"),re=Symbol.for("react.offscreen"),V=Symbol.iterator;function me(n){return n===null||typeof n!="object"?null:(n=V&&n[V]||n["@@iterator"],typeof n=="function"?n:null)}var ie=Object.assign,P;function B(n){if(P===void 0)try{throw Error()}catch(a){var i=a.stack.trim().match(/\n( *(at )?)/);P=i&&i[1]||""}return`
`+P+n}var Z=!1;function ue(n,i){if(!n||Z)return"";Z=!0;var a=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{if(i)if(i=function(){throw Error()},Object.defineProperty(i.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(i,[])}catch(de){var c=de}Reflect.construct(n,[],i)}else{try{i.call()}catch(de){c=de}n.call(i.prototype)}else{try{throw Error()}catch(de){c=de}n()}}catch(de){if(de&&c&&typeof de.stack=="string"){for(var h=de.stack.split(`
`),m=c.stack.split(`
`),E=h.length-1,k=m.length-1;1<=E&&0<=k&&h[E]!==m[k];)k--;for(;1<=E&&0<=k;E--,k--)if(h[E]!==m[k]){if(E!==1||k!==1)do if(E--,k--,0>k||h[E]!==m[k]){var G=`
`+h[E].replace(" at new "," at ");return n.displayName&&G.includes("<anonymous>")&&(G=G.replace("<anonymous>",n.displayName)),G}while(1<=E&&0<=k);break}}}finally{Z=!1,Error.prepareStackTrace=a}return(n=n?n.displayName||n.name:"")?B(n):""}function he(n){switch(n.tag){case 5:return B(n.type);case 16:return B("Lazy");case 13:return B("Suspense");case 19:return B("SuspenseList");case 0:case 2:case 15:return n=ue(n.type,!1),n;case 11:return n=ue(n.type.render,!1),n;case 1:return n=ue(n.type,!0),n;default:return""}}function K(n){if(n==null)return null;if(typeof n=="function")return n.displayName||n.name||null;if(typeof n=="string")return n;switch(n){case I:return"Fragment";case H:return"Portal";case C:return"Profiler";case N:return"StrictMode";case ee:return"Suspense";case le:return"SuspenseList"}if(typeof n=="object")switch(n.$$typeof){case F:return(n.displayName||"Context")+".Consumer";case T:return(n._context.displayName||"Context")+".Provider";case $:var i=n.render;return n=n.displayName,n||(n=i.displayName||i.name||"",n=n!==""?"ForwardRef("+n+")":"ForwardRef"),n;case ne:return i=n.displayName||null,i!==null?i:K(n.type)||"Memo";case ce:i=n._payload,n=n._init;try{return K(n(i))}catch{}}return null}function oe(n){var i=n.type;switch(n.tag){case 24:return"Cache";case 9:return(i.displayName||"Context")+".Consumer";case 10:return(i._context.displayName||"Context")+".Provider";case 18:return"DehydratedFragment";case 11:return n=i.render,n=n.displayName||n.name||"",i.displayName||(n!==""?"ForwardRef("+n+")":"ForwardRef");case 7:return"Fragment";case 5:return i;case 4:return"Portal";case 3:return"Root";case 6:return"Text";case 16:return K(i);case 8:return i===N?"StrictMode":"Mode";case 22:return"Offscreen";case 12:return"Profiler";case 21:return"Scope";case 13:return"Suspense";case 19:return"SuspenseList";case 25:return"TracingMarker";case 1:case 0:case 17:case 2:case 14:case 15:if(typeof i=="function")return i.displayName||i.name||null;if(typeof i=="string")return i}return null}function Ee(n){switch(typeof n){case"boolean":case"number":case"string":case"undefined":return n;case"object":return n;default:return""}}function ye(n){var i=n.type;return(n=n.nodeName)&&n.toLowerCase()==="input"&&(i==="checkbox"||i==="radio")}function we(n){var i=ye(n)?"checked":"value",a=Object.getOwnPropertyDescriptor(n.constructor.prototype,i),c=""+n[i];if(!n.hasOwnProperty(i)&&typeof a<"u"&&typeof a.get=="function"&&typeof a.set=="function"){var h=a.get,m=a.set;return Object.defineProperty(n,i,{configurable:!0,get:function(){return h.call(this)},set:function(E){c=""+E,m.call(this,E)}}),Object.defineProperty(n,i,{enumerable:a.enumerable}),{getValue:function(){return c},setValue:function(E){c=""+E},stopTracking:function(){n._valueTracker=null,delete n[i]}}}}function tt(n){n._valueTracker||(n._valueTracker=we(n))}function at(n){if(!n)return!1;var i=n._valueTracker;if(!i)return!0;var a=i.getValue(),c="";return n&&(c=ye(n)?n.checked?"true":"false":n.value),n=c,n!==a?(i.setValue(n),!0):!1}function U(n){if(n=n||(typeof document<"u"?document:void 0),typeof n>"u")return null;try{return n.activeElement||n.body}catch{return n.body}}function Me(n,i){var a=i.checked;return ie({},i,{defaultChecked:void 0,defaultValue:void 0,value:void 0,checked:a??n._wrapperState.initialChecked})}function _e(n,i){var a=i.defaultValue==null?"":i.defaultValue,c=i.checked!=null?i.checked:i.defaultChecked;a=Ee(i.value!=null?i.value:a),n._wrapperState={initialChecked:c,initialValue:a,controlled:i.type==="checkbox"||i.type==="radio"?i.checked!=null:i.value!=null}}function Se(n,i){i=i.checked,i!=null&&D(n,"checked",i,!1)}function fe(n,i){Se(n,i);var a=Ee(i.value),c=i.type;if(a!=null)c==="number"?(a===0&&n.value===""||n.value!=a)&&(n.value=""+a):n.value!==""+a&&(n.value=""+a);else if(c==="submit"||c==="reset"){n.removeAttribute("value");return}i.hasOwnProperty("value")?xe(n,i.type,a):i.hasOwnProperty("defaultValue")&&xe(n,i.type,Ee(i.defaultValue)),i.checked==null&&i.defaultChecked!=null&&(n.defaultChecked=!!i.defaultChecked)}function be(n,i,a){if(i.hasOwnProperty("value")||i.hasOwnProperty("defaultValue")){var c=i.type;if(!(c!=="submit"&&c!=="reset"||i.value!==void 0&&i.value!==null))return;i=""+n._wrapperState.initialValue,a||i===n.value||(n.value=i),n.defaultValue=i}a=n.name,a!==""&&(n.name=""),n.defaultChecked=!!n._wrapperState.initialChecked,a!==""&&(n.name=a)}function xe(n,i,a){(i!=="number"||U(n.ownerDocument)!==n)&&(a==null?n.defaultValue=""+n._wrapperState.initialValue:n.defaultValue!==""+a&&(n.defaultValue=""+a))}var Re=Array.isArray;function ct(n,i,a,c){if(n=n.options,i){i={};for(var h=0;h<a.length;h++)i["$"+a[h]]=!0;for(a=0;a<n.length;a++)h=i.hasOwnProperty("$"+n[a].value),n[a].selected!==h&&(n[a].selected=h),h&&c&&(n[a].defaultSelected=!0)}else{for(a=""+Ee(a),i=null,h=0;h<n.length;h++){if(n[h].value===a){n[h].selected=!0,c&&(n[h].defaultSelected=!0);return}i!==null||n[h].disabled||(i=n[h])}i!==null&&(i.selected=!0)}}function ft(n,i){if(i.dangerouslySetInnerHTML!=null)throw Error(t(91));return ie({},i,{value:void 0,defaultValue:void 0,children:""+n._wrapperState.initialValue})}function L(n,i){var a=i.value;if(a==null){if(a=i.children,i=i.defaultValue,a!=null){if(i!=null)throw Error(t(92));if(Re(a)){if(1<a.length)throw Error(t(93));a=a[0]}i=a}i==null&&(i=""),a=i}n._wrapperState={initialValue:Ee(a)}}function w(n,i){var a=Ee(i.value),c=Ee(i.defaultValue);a!=null&&(a=""+a,a!==n.value&&(n.value=a),i.defaultValue==null&&n.defaultValue!==a&&(n.defaultValue=a)),c!=null&&(n.defaultValue=""+c)}function J(n){var i=n.textContent;i===n._wrapperState.initialValue&&i!==""&&i!==null&&(n.value=i)}function ge(n){switch(n){case"svg":return"http://www.w3.org/2000/svg";case"math":return"http://www.w3.org/1998/Math/MathML";default:return"http://www.w3.org/1999/xhtml"}}function Ae(n,i){return n==null||n==="http://www.w3.org/1999/xhtml"?ge(i):n==="http://www.w3.org/2000/svg"&&i==="foreignObject"?"http://www.w3.org/1999/xhtml":n}var ve,Je=(function(n){return typeof MSApp<"u"&&MSApp.execUnsafeLocalFunction?function(i,a,c,h){MSApp.execUnsafeLocalFunction(function(){return n(i,a,c,h)})}:n})(function(n,i){if(n.namespaceURI!=="http://www.w3.org/2000/svg"||"innerHTML"in n)n.innerHTML=i;else{for(ve=ve||document.createElement("div"),ve.innerHTML="<svg>"+i.valueOf().toString()+"</svg>",i=ve.firstChild;n.firstChild;)n.removeChild(n.firstChild);for(;i.firstChild;)n.appendChild(i.firstChild)}});function Le(n,i){if(i){var a=n.firstChild;if(a&&a===n.lastChild&&a.nodeType===3){a.nodeValue=i;return}}n.textContent=i}var Ke={animationIterationCount:!0,aspectRatio:!0,borderImageOutset:!0,borderImageSlice:!0,borderImageWidth:!0,boxFlex:!0,boxFlexGroup:!0,boxOrdinalGroup:!0,columnCount:!0,columns:!0,flex:!0,flexGrow:!0,flexPositive:!0,flexShrink:!0,flexNegative:!0,flexOrder:!0,gridArea:!0,gridRow:!0,gridRowEnd:!0,gridRowSpan:!0,gridRowStart:!0,gridColumn:!0,gridColumnEnd:!0,gridColumnSpan:!0,gridColumnStart:!0,fontWeight:!0,lineClamp:!0,lineHeight:!0,opacity:!0,order:!0,orphans:!0,tabSize:!0,widows:!0,zIndex:!0,zoom:!0,fillOpacity:!0,floodOpacity:!0,stopOpacity:!0,strokeDasharray:!0,strokeDashoffset:!0,strokeMiterlimit:!0,strokeOpacity:!0,strokeWidth:!0},nt=["Webkit","ms","Moz","O"];Object.keys(Ke).forEach(function(n){nt.forEach(function(i){i=i+n.charAt(0).toUpperCase()+n.substring(1),Ke[i]=Ke[n]})});function Ie(n,i,a){return i==null||typeof i=="boolean"||i===""?"":a||typeof i!="number"||i===0||Ke.hasOwnProperty(n)&&Ke[n]?(""+i).trim():i+"px"}function He(n,i){n=n.style;for(var a in i)if(i.hasOwnProperty(a)){var c=a.indexOf("--")===0,h=Ie(a,i[a],c);a==="float"&&(a="cssFloat"),c?n.setProperty(a,h):n[a]=h}}var ut=ie({menuitem:!0},{area:!0,base:!0,br:!0,col:!0,embed:!0,hr:!0,img:!0,input:!0,keygen:!0,link:!0,meta:!0,param:!0,source:!0,track:!0,wbr:!0});function Ze(n,i){if(i){if(ut[n]&&(i.children!=null||i.dangerouslySetInnerHTML!=null))throw Error(t(137,n));if(i.dangerouslySetInnerHTML!=null){if(i.children!=null)throw Error(t(60));if(typeof i.dangerouslySetInnerHTML!="object"||!("__html"in i.dangerouslySetInnerHTML))throw Error(t(61))}if(i.style!=null&&typeof i.style!="object")throw Error(t(62))}}function Ve(n,i){if(n.indexOf("-")===-1)return typeof i.is=="string";switch(n){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var ht=null;function X(n){return n=n.target||n.srcElement||window,n.correspondingUseElement&&(n=n.correspondingUseElement),n.nodeType===3?n.parentNode:n}var Ue=null,ke=null,Xe=null;function De(n){if(n=To(n)){if(typeof Ue!="function")throw Error(t(280));var i=n.stateNode;i&&(i=Aa(i),Ue(n.stateNode,n.type,i))}}function Te(n){ke?Xe?Xe.push(n):Xe=[n]:ke=n}function et(){if(ke){var n=ke,i=Xe;if(Xe=ke=null,De(n),i)for(n=0;n<i.length;n++)De(i[n])}}function xt(n,i){return n(i)}function Ne(){}var qe=!1;function Mt(n,i,a){if(qe)return n(i,a);qe=!0;try{return xt(n,i,a)}finally{qe=!1,(ke!==null||Xe!==null)&&(Ne(),et())}}function vt(n,i){var a=n.stateNode;if(a===null)return null;var c=Aa(a);if(c===null)return null;a=c[i];e:switch(i){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(c=!c.disabled)||(n=n.type,c=!(n==="button"||n==="input"||n==="select"||n==="textarea")),n=!c;break e;default:n=!1}if(n)return null;if(a&&typeof a!="function")throw Error(t(231,i,typeof a));return a}var Lt=!1;if(f)try{var Wt={};Object.defineProperty(Wt,"passive",{get:function(){Lt=!0}}),window.addEventListener("test",Wt,Wt),window.removeEventListener("test",Wt,Wt)}catch{Lt=!1}function xn(n,i,a,c,h,m,E,k,G){var de=Array.prototype.slice.call(arguments,3);try{i.apply(a,de)}catch(Pe){this.onError(Pe)}}var un=!1,fn=null,Jt=!1,$i=null,Ki={onError:function(n){un=!0,fn=n}};function Zi(n,i,a,c,h,m,E,k,G){un=!1,fn=null,xn.apply(Ki,arguments)}function ls(n,i,a,c,h,m,E,k,G){if(Zi.apply(this,arguments),un){if(un){var de=fn;un=!1,fn=null}else throw Error(t(198));Jt||(Jt=!0,$i=de)}}function Wn(n){var i=n,a=n;if(n.alternate)for(;i.return;)i=i.return;else{n=i;do i=n,(i.flags&4098)!==0&&(a=i.return),n=i.return;while(n)}return i.tag===3?a:null}function Ji(n){if(n.tag===13){var i=n.memoizedState;if(i===null&&(n=n.alternate,n!==null&&(i=n.memoizedState)),i!==null)return i.dehydrated}return null}function Qi(n){if(Wn(n)!==n)throw Error(t(188))}function cs(n){var i=n.alternate;if(!i){if(i=Wn(n),i===null)throw Error(t(188));return i!==n?null:n}for(var a=n,c=i;;){var h=a.return;if(h===null)break;var m=h.alternate;if(m===null){if(c=h.return,c!==null){a=c;continue}break}if(h.child===m.child){for(m=h.child;m;){if(m===a)return Qi(h),n;if(m===c)return Qi(h),i;m=m.sibling}throw Error(t(188))}if(a.return!==c.return)a=h,c=m;else{for(var E=!1,k=h.child;k;){if(k===a){E=!0,a=h,c=m;break}if(k===c){E=!0,c=h,a=m;break}k=k.sibling}if(!E){for(k=m.child;k;){if(k===a){E=!0,a=m,c=h;break}if(k===c){E=!0,c=m,a=h;break}k=k.sibling}if(!E)throw Error(t(189))}}if(a.alternate!==c)throw Error(t(190))}if(a.tag!==3)throw Error(t(188));return a.stateNode.current===a?n:i}function Pr(n){return n=cs(n),n!==null?Lr(n):null}function Lr(n){if(n.tag===5||n.tag===6)return n;for(n=n.child;n!==null;){var i=Lr(n);if(i!==null)return i;n=n.sibling}return null}var b=e.unstable_scheduleCallback,j=e.unstable_cancelCallback,ae=e.unstable_shouldYield,pe=e.unstable_requestPaint,Y=e.unstable_now,Be=e.unstable_getCurrentPriorityLevel,We=e.unstable_ImmediatePriority,it=e.unstable_UserBlockingPriority,Ye=e.unstable_NormalPriority,gt=e.unstable_LowPriority,_t=e.unstable_IdlePriority,lt=null,yt=null;function Ut(n){if(yt&&typeof yt.onCommitFiberRoot=="function")try{yt.onCommitFiberRoot(lt,n,void 0,(n.current.flags&128)===128)}catch{}}var bt=Math.clz32?Math.clz32:dt,Bt=Math.log,Ft=Math.LN2;function dt(n){return n>>>=0,n===0?32:31-(Bt(n)/Ft|0)|0}var Ot=64,At=4194304;function rn(n){switch(n&-n){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return n&4194240;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return n&130023424;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 1073741824;default:return n}}function si(n,i){var a=n.pendingLanes;if(a===0)return 0;var c=0,h=n.suspendedLanes,m=n.pingedLanes,E=a&268435455;if(E!==0){var k=E&~h;k!==0?c=rn(k):(m&=E,m!==0&&(c=rn(m)))}else E=a&~h,E!==0?c=rn(E):m!==0&&(c=rn(m));if(c===0)return 0;if(i!==0&&i!==c&&(i&h)===0&&(h=c&-c,m=i&-i,h>=m||h===16&&(m&4194240)!==0))return i;if((c&4)!==0&&(c|=a&16),i=n.entangledLanes,i!==0)for(n=n.entanglements,i&=c;0<i;)a=31-bt(i),h=1<<a,c|=n[a],i&=~h;return c}function Cn(n,i){switch(n){case 1:case 2:case 4:return i+250;case 8:case 16:case 32:case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return i+5e3;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return-1;case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function Dr(n,i){for(var a=n.suspendedLanes,c=n.pingedLanes,h=n.expirationTimes,m=n.pendingLanes;0<m;){var E=31-bt(m),k=1<<E,G=h[E];G===-1?((k&a)===0||(k&c)!==0)&&(h[E]=Cn(k,i)):G<=i&&(n.expiredLanes|=k),m&=~k}}function zt(n){return n=n.pendingLanes&-1073741825,n!==0?n:n&1073741824?1073741824:0}function bn(){var n=Ot;return Ot<<=1,(Ot&4194240)===0&&(Ot=64),n}function yn(n){for(var i=[],a=0;31>a;a++)i.push(n);return i}function Qt(n,i,a){n.pendingLanes|=i,i!==536870912&&(n.suspendedLanes=0,n.pingedLanes=0),n=n.eventTimes,i=31-bt(i),n[i]=a}function Sn(n,i){var a=n.pendingLanes&~i;n.pendingLanes=i,n.suspendedLanes=0,n.pingedLanes=0,n.expiredLanes&=i,n.mutableReadLanes&=i,n.entangledLanes&=i,i=n.entanglements;var c=n.eventTimes;for(n=n.expirationTimes;0<a;){var h=31-bt(a),m=1<<h;i[h]=0,c[h]=-1,n[h]=-1,a&=~m}}function Nr(n,i){var a=n.entangledLanes|=i;for(n=n.entanglements;a;){var c=31-bt(a),h=1<<c;h&i|n[c]&i&&(n[c]|=i),a&=~h}}var Rt=0;function Ud(n){return n&=-n,1<n?4<n?(n&268435455)!==0?16:536870912:4:1}var Fd,rc,Od,kd,Bd,sc=!1,fa=[],er=null,tr=null,nr=null,lo=new Map,co=new Map,ir=[],Mg="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");function zd(n,i){switch(n){case"focusin":case"focusout":er=null;break;case"dragenter":case"dragleave":tr=null;break;case"mouseover":case"mouseout":nr=null;break;case"pointerover":case"pointerout":lo.delete(i.pointerId);break;case"gotpointercapture":case"lostpointercapture":co.delete(i.pointerId)}}function uo(n,i,a,c,h,m){return n===null||n.nativeEvent!==m?(n={blockedOn:i,domEventName:a,eventSystemFlags:c,nativeEvent:m,targetContainers:[h]},i!==null&&(i=To(i),i!==null&&rc(i)),n):(n.eventSystemFlags|=c,i=n.targetContainers,h!==null&&i.indexOf(h)===-1&&i.push(h),n)}function Eg(n,i,a,c,h){switch(i){case"focusin":return er=uo(er,n,i,a,c,h),!0;case"dragenter":return tr=uo(tr,n,i,a,c,h),!0;case"mouseover":return nr=uo(nr,n,i,a,c,h),!0;case"pointerover":var m=h.pointerId;return lo.set(m,uo(lo.get(m)||null,n,i,a,c,h)),!0;case"gotpointercapture":return m=h.pointerId,co.set(m,uo(co.get(m)||null,n,i,a,c,h)),!0}return!1}function Hd(n){var i=Ir(n.target);if(i!==null){var a=Wn(i);if(a!==null){if(i=a.tag,i===13){if(i=Ji(a),i!==null){n.blockedOn=i,Bd(n.priority,function(){Od(a)});return}}else if(i===3&&a.stateNode.current.memoizedState.isDehydrated){n.blockedOn=a.tag===3?a.stateNode.containerInfo:null;return}}}n.blockedOn=null}function da(n){if(n.blockedOn!==null)return!1;for(var i=n.targetContainers;0<i.length;){var a=ac(n.domEventName,n.eventSystemFlags,i[0],n.nativeEvent);if(a===null){a=n.nativeEvent;var c=new a.constructor(a.type,a);ht=c,a.target.dispatchEvent(c),ht=null}else return i=To(a),i!==null&&rc(i),n.blockedOn=a,!1;i.shift()}return!0}function Vd(n,i,a){da(n)&&a.delete(i)}function wg(){sc=!1,er!==null&&da(er)&&(er=null),tr!==null&&da(tr)&&(tr=null),nr!==null&&da(nr)&&(nr=null),lo.forEach(Vd),co.forEach(Vd)}function fo(n,i){n.blockedOn===i&&(n.blockedOn=null,sc||(sc=!0,e.unstable_scheduleCallback(e.unstable_NormalPriority,wg)))}function ho(n){function i(h){return fo(h,n)}if(0<fa.length){fo(fa[0],n);for(var a=1;a<fa.length;a++){var c=fa[a];c.blockedOn===n&&(c.blockedOn=null)}}for(er!==null&&fo(er,n),tr!==null&&fo(tr,n),nr!==null&&fo(nr,n),lo.forEach(i),co.forEach(i),a=0;a<ir.length;a++)c=ir[a],c.blockedOn===n&&(c.blockedOn=null);for(;0<ir.length&&(a=ir[0],a.blockedOn===null);)Hd(a),a.blockedOn===null&&ir.shift()}var us=R.ReactCurrentBatchConfig,ha=!0;function Tg(n,i,a,c){var h=Rt,m=us.transition;us.transition=null;try{Rt=1,oc(n,i,a,c)}finally{Rt=h,us.transition=m}}function Ag(n,i,a,c){var h=Rt,m=us.transition;us.transition=null;try{Rt=4,oc(n,i,a,c)}finally{Rt=h,us.transition=m}}function oc(n,i,a,c){if(ha){var h=ac(n,i,a,c);if(h===null)wc(n,i,c,pa,a),zd(n,c);else if(Eg(h,n,i,a,c))c.stopPropagation();else if(zd(n,c),i&4&&-1<Mg.indexOf(n)){for(;h!==null;){var m=To(h);if(m!==null&&Fd(m),m=ac(n,i,a,c),m===null&&wc(n,i,c,pa,a),m===h)break;h=m}h!==null&&c.stopPropagation()}else wc(n,i,c,null,a)}}var pa=null;function ac(n,i,a,c){if(pa=null,n=X(c),n=Ir(n),n!==null)if(i=Wn(n),i===null)n=null;else if(a=i.tag,a===13){if(n=Ji(i),n!==null)return n;n=null}else if(a===3){if(i.stateNode.current.memoizedState.isDehydrated)return i.tag===3?i.stateNode.containerInfo:null;n=null}else i!==n&&(n=null);return pa=n,null}function Gd(n){switch(n){case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 1;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"toggle":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 4;case"message":switch(Be()){case We:return 1;case it:return 4;case Ye:case gt:return 16;case _t:return 536870912;default:return 16}default:return 16}}var rr=null,lc=null,ma=null;function Wd(){if(ma)return ma;var n,i=lc,a=i.length,c,h="value"in rr?rr.value:rr.textContent,m=h.length;for(n=0;n<a&&i[n]===h[n];n++);var E=a-n;for(c=1;c<=E&&i[a-c]===h[m-c];c++);return ma=h.slice(n,1<c?1-c:void 0)}function ga(n){var i=n.keyCode;return"charCode"in n?(n=n.charCode,n===0&&i===13&&(n=13)):n=i,n===10&&(n=13),32<=n||n===13?n:0}function va(){return!0}function Xd(){return!1}function Xn(n){function i(a,c,h,m,E){this._reactName=a,this._targetInst=h,this.type=c,this.nativeEvent=m,this.target=E,this.currentTarget=null;for(var k in n)n.hasOwnProperty(k)&&(a=n[k],this[k]=a?a(m):m[k]);return this.isDefaultPrevented=(m.defaultPrevented!=null?m.defaultPrevented:m.returnValue===!1)?va:Xd,this.isPropagationStopped=Xd,this}return ie(i.prototype,{preventDefault:function(){this.defaultPrevented=!0;var a=this.nativeEvent;a&&(a.preventDefault?a.preventDefault():typeof a.returnValue!="unknown"&&(a.returnValue=!1),this.isDefaultPrevented=va)},stopPropagation:function(){var a=this.nativeEvent;a&&(a.stopPropagation?a.stopPropagation():typeof a.cancelBubble!="unknown"&&(a.cancelBubble=!0),this.isPropagationStopped=va)},persist:function(){},isPersistent:va}),i}var fs={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(n){return n.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},cc=Xn(fs),po=ie({},fs,{view:0,detail:0}),Rg=Xn(po),uc,fc,mo,_a=ie({},po,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:hc,button:0,buttons:0,relatedTarget:function(n){return n.relatedTarget===void 0?n.fromElement===n.srcElement?n.toElement:n.fromElement:n.relatedTarget},movementX:function(n){return"movementX"in n?n.movementX:(n!==mo&&(mo&&n.type==="mousemove"?(uc=n.screenX-mo.screenX,fc=n.screenY-mo.screenY):fc=uc=0,mo=n),uc)},movementY:function(n){return"movementY"in n?n.movementY:fc}}),jd=Xn(_a),Cg=ie({},_a,{dataTransfer:0}),bg=Xn(Cg),Pg=ie({},po,{relatedTarget:0}),dc=Xn(Pg),Lg=ie({},fs,{animationName:0,elapsedTime:0,pseudoElement:0}),Dg=Xn(Lg),Ng=ie({},fs,{clipboardData:function(n){return"clipboardData"in n?n.clipboardData:window.clipboardData}}),Ig=Xn(Ng),Ug=ie({},fs,{data:0}),qd=Xn(Ug),Fg={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},Og={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},kg={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function Bg(n){var i=this.nativeEvent;return i.getModifierState?i.getModifierState(n):(n=kg[n])?!!i[n]:!1}function hc(){return Bg}var zg=ie({},po,{key:function(n){if(n.key){var i=Fg[n.key]||n.key;if(i!=="Unidentified")return i}return n.type==="keypress"?(n=ga(n),n===13?"Enter":String.fromCharCode(n)):n.type==="keydown"||n.type==="keyup"?Og[n.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:hc,charCode:function(n){return n.type==="keypress"?ga(n):0},keyCode:function(n){return n.type==="keydown"||n.type==="keyup"?n.keyCode:0},which:function(n){return n.type==="keypress"?ga(n):n.type==="keydown"||n.type==="keyup"?n.keyCode:0}}),Hg=Xn(zg),Vg=ie({},_a,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),Yd=Xn(Vg),Gg=ie({},po,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:hc}),Wg=Xn(Gg),Xg=ie({},fs,{propertyName:0,elapsedTime:0,pseudoElement:0}),jg=Xn(Xg),qg=ie({},_a,{deltaX:function(n){return"deltaX"in n?n.deltaX:"wheelDeltaX"in n?-n.wheelDeltaX:0},deltaY:function(n){return"deltaY"in n?n.deltaY:"wheelDeltaY"in n?-n.wheelDeltaY:"wheelDelta"in n?-n.wheelDelta:0},deltaZ:0,deltaMode:0}),Yg=Xn(qg),$g=[9,13,27,32],pc=f&&"CompositionEvent"in window,go=null;f&&"documentMode"in document&&(go=document.documentMode);var Kg=f&&"TextEvent"in window&&!go,$d=f&&(!pc||go&&8<go&&11>=go),Kd=" ",Zd=!1;function Jd(n,i){switch(n){case"keyup":return $g.indexOf(i.keyCode)!==-1;case"keydown":return i.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function Qd(n){return n=n.detail,typeof n=="object"&&"data"in n?n.data:null}var ds=!1;function Zg(n,i){switch(n){case"compositionend":return Qd(i);case"keypress":return i.which!==32?null:(Zd=!0,Kd);case"textInput":return n=i.data,n===Kd&&Zd?null:n;default:return null}}function Jg(n,i){if(ds)return n==="compositionend"||!pc&&Jd(n,i)?(n=Wd(),ma=lc=rr=null,ds=!1,n):null;switch(n){case"paste":return null;case"keypress":if(!(i.ctrlKey||i.altKey||i.metaKey)||i.ctrlKey&&i.altKey){if(i.char&&1<i.char.length)return i.char;if(i.which)return String.fromCharCode(i.which)}return null;case"compositionend":return $d&&i.locale!=="ko"?null:i.data;default:return null}}var Qg={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function eh(n){var i=n&&n.nodeName&&n.nodeName.toLowerCase();return i==="input"?!!Qg[n.type]:i==="textarea"}function th(n,i,a,c){Te(c),i=Ea(i,"onChange"),0<i.length&&(a=new cc("onChange","change",null,a,c),n.push({event:a,listeners:i}))}var vo=null,_o=null;function ev(n){xh(n,0)}function xa(n){var i=vs(n);if(at(i))return n}function tv(n,i){if(n==="change")return i}var nh=!1;if(f){var mc;if(f){var gc="oninput"in document;if(!gc){var ih=document.createElement("div");ih.setAttribute("oninput","return;"),gc=typeof ih.oninput=="function"}mc=gc}else mc=!1;nh=mc&&(!document.documentMode||9<document.documentMode)}function rh(){vo&&(vo.detachEvent("onpropertychange",sh),_o=vo=null)}function sh(n){if(n.propertyName==="value"&&xa(_o)){var i=[];th(i,_o,n,X(n)),Mt(ev,i)}}function nv(n,i,a){n==="focusin"?(rh(),vo=i,_o=a,vo.attachEvent("onpropertychange",sh)):n==="focusout"&&rh()}function iv(n){if(n==="selectionchange"||n==="keyup"||n==="keydown")return xa(_o)}function rv(n,i){if(n==="click")return xa(i)}function sv(n,i){if(n==="input"||n==="change")return xa(i)}function ov(n,i){return n===i&&(n!==0||1/n===1/i)||n!==n&&i!==i}var oi=typeof Object.is=="function"?Object.is:ov;function xo(n,i){if(oi(n,i))return!0;if(typeof n!="object"||n===null||typeof i!="object"||i===null)return!1;var a=Object.keys(n),c=Object.keys(i);if(a.length!==c.length)return!1;for(c=0;c<a.length;c++){var h=a[c];if(!d.call(i,h)||!oi(n[h],i[h]))return!1}return!0}function oh(n){for(;n&&n.firstChild;)n=n.firstChild;return n}function ah(n,i){var a=oh(n);n=0;for(var c;a;){if(a.nodeType===3){if(c=n+a.textContent.length,n<=i&&c>=i)return{node:a,offset:i-n};n=c}e:{for(;a;){if(a.nextSibling){a=a.nextSibling;break e}a=a.parentNode}a=void 0}a=oh(a)}}function lh(n,i){return n&&i?n===i?!0:n&&n.nodeType===3?!1:i&&i.nodeType===3?lh(n,i.parentNode):"contains"in n?n.contains(i):n.compareDocumentPosition?!!(n.compareDocumentPosition(i)&16):!1:!1}function ch(){for(var n=window,i=U();i instanceof n.HTMLIFrameElement;){try{var a=typeof i.contentWindow.location.href=="string"}catch{a=!1}if(a)n=i.contentWindow;else break;i=U(n.document)}return i}function vc(n){var i=n&&n.nodeName&&n.nodeName.toLowerCase();return i&&(i==="input"&&(n.type==="text"||n.type==="search"||n.type==="tel"||n.type==="url"||n.type==="password")||i==="textarea"||n.contentEditable==="true")}function av(n){var i=ch(),a=n.focusedElem,c=n.selectionRange;if(i!==a&&a&&a.ownerDocument&&lh(a.ownerDocument.documentElement,a)){if(c!==null&&vc(a)){if(i=c.start,n=c.end,n===void 0&&(n=i),"selectionStart"in a)a.selectionStart=i,a.selectionEnd=Math.min(n,a.value.length);else if(n=(i=a.ownerDocument||document)&&i.defaultView||window,n.getSelection){n=n.getSelection();var h=a.textContent.length,m=Math.min(c.start,h);c=c.end===void 0?m:Math.min(c.end,h),!n.extend&&m>c&&(h=c,c=m,m=h),h=ah(a,m);var E=ah(a,c);h&&E&&(n.rangeCount!==1||n.anchorNode!==h.node||n.anchorOffset!==h.offset||n.focusNode!==E.node||n.focusOffset!==E.offset)&&(i=i.createRange(),i.setStart(h.node,h.offset),n.removeAllRanges(),m>c?(n.addRange(i),n.extend(E.node,E.offset)):(i.setEnd(E.node,E.offset),n.addRange(i)))}}for(i=[],n=a;n=n.parentNode;)n.nodeType===1&&i.push({element:n,left:n.scrollLeft,top:n.scrollTop});for(typeof a.focus=="function"&&a.focus(),a=0;a<i.length;a++)n=i[a],n.element.scrollLeft=n.left,n.element.scrollTop=n.top}}var lv=f&&"documentMode"in document&&11>=document.documentMode,hs=null,_c=null,yo=null,xc=!1;function uh(n,i,a){var c=a.window===a?a.document:a.nodeType===9?a:a.ownerDocument;xc||hs==null||hs!==U(c)||(c=hs,"selectionStart"in c&&vc(c)?c={start:c.selectionStart,end:c.selectionEnd}:(c=(c.ownerDocument&&c.ownerDocument.defaultView||window).getSelection(),c={anchorNode:c.anchorNode,anchorOffset:c.anchorOffset,focusNode:c.focusNode,focusOffset:c.focusOffset}),yo&&xo(yo,c)||(yo=c,c=Ea(_c,"onSelect"),0<c.length&&(i=new cc("onSelect","select",null,i,a),n.push({event:i,listeners:c}),i.target=hs)))}function ya(n,i){var a={};return a[n.toLowerCase()]=i.toLowerCase(),a["Webkit"+n]="webkit"+i,a["Moz"+n]="moz"+i,a}var ps={animationend:ya("Animation","AnimationEnd"),animationiteration:ya("Animation","AnimationIteration"),animationstart:ya("Animation","AnimationStart"),transitionend:ya("Transition","TransitionEnd")},yc={},fh={};f&&(fh=document.createElement("div").style,"AnimationEvent"in window||(delete ps.animationend.animation,delete ps.animationiteration.animation,delete ps.animationstart.animation),"TransitionEvent"in window||delete ps.transitionend.transition);function Sa(n){if(yc[n])return yc[n];if(!ps[n])return n;var i=ps[n],a;for(a in i)if(i.hasOwnProperty(a)&&a in fh)return yc[n]=i[a];return n}var dh=Sa("animationend"),hh=Sa("animationiteration"),ph=Sa("animationstart"),mh=Sa("transitionend"),gh=new Map,vh="abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");function sr(n,i){gh.set(n,i),l(i,[n])}for(var Sc=0;Sc<vh.length;Sc++){var Mc=vh[Sc],cv=Mc.toLowerCase(),uv=Mc[0].toUpperCase()+Mc.slice(1);sr(cv,"on"+uv)}sr(dh,"onAnimationEnd"),sr(hh,"onAnimationIteration"),sr(ph,"onAnimationStart"),sr("dblclick","onDoubleClick"),sr("focusin","onFocus"),sr("focusout","onBlur"),sr(mh,"onTransitionEnd"),u("onMouseEnter",["mouseout","mouseover"]),u("onMouseLeave",["mouseout","mouseover"]),u("onPointerEnter",["pointerout","pointerover"]),u("onPointerLeave",["pointerout","pointerover"]),l("onChange","change click focusin focusout input keydown keyup selectionchange".split(" ")),l("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")),l("onBeforeInput",["compositionend","keypress","textInput","paste"]),l("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" ")),l("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" ")),l("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var So="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),fv=new Set("cancel close invalid load scroll toggle".split(" ").concat(So));function _h(n,i,a){var c=n.type||"unknown-event";n.currentTarget=a,ls(c,i,void 0,n),n.currentTarget=null}function xh(n,i){i=(i&4)!==0;for(var a=0;a<n.length;a++){var c=n[a],h=c.event;c=c.listeners;e:{var m=void 0;if(i)for(var E=c.length-1;0<=E;E--){var k=c[E],G=k.instance,de=k.currentTarget;if(k=k.listener,G!==m&&h.isPropagationStopped())break e;_h(h,k,de),m=G}else for(E=0;E<c.length;E++){if(k=c[E],G=k.instance,de=k.currentTarget,k=k.listener,G!==m&&h.isPropagationStopped())break e;_h(h,k,de),m=G}}}if(Jt)throw n=$i,Jt=!1,$i=null,n}function Vt(n,i){var a=i[Pc];a===void 0&&(a=i[Pc]=new Set);var c=n+"__bubble";a.has(c)||(yh(i,n,2,!1),a.add(c))}function Ec(n,i,a){var c=0;i&&(c|=4),yh(a,n,c,i)}var Ma="_reactListening"+Math.random().toString(36).slice(2);function Mo(n){if(!n[Ma]){n[Ma]=!0,r.forEach(function(a){a!=="selectionchange"&&(fv.has(a)||Ec(a,!1,n),Ec(a,!0,n))});var i=n.nodeType===9?n:n.ownerDocument;i===null||i[Ma]||(i[Ma]=!0,Ec("selectionchange",!1,i))}}function yh(n,i,a,c){switch(Gd(i)){case 1:var h=Tg;break;case 4:h=Ag;break;default:h=oc}a=h.bind(null,i,a,n),h=void 0,!Lt||i!=="touchstart"&&i!=="touchmove"&&i!=="wheel"||(h=!0),c?h!==void 0?n.addEventListener(i,a,{capture:!0,passive:h}):n.addEventListener(i,a,!0):h!==void 0?n.addEventListener(i,a,{passive:h}):n.addEventListener(i,a,!1)}function wc(n,i,a,c,h){var m=c;if((i&1)===0&&(i&2)===0&&c!==null)e:for(;;){if(c===null)return;var E=c.tag;if(E===3||E===4){var k=c.stateNode.containerInfo;if(k===h||k.nodeType===8&&k.parentNode===h)break;if(E===4)for(E=c.return;E!==null;){var G=E.tag;if((G===3||G===4)&&(G=E.stateNode.containerInfo,G===h||G.nodeType===8&&G.parentNode===h))return;E=E.return}for(;k!==null;){if(E=Ir(k),E===null)return;if(G=E.tag,G===5||G===6){c=m=E;continue e}k=k.parentNode}}c=c.return}Mt(function(){var de=m,Pe=X(a),Fe=[];e:{var Ce=gh.get(n);if(Ce!==void 0){var $e=cc,rt=n;switch(n){case"keypress":if(ga(a)===0)break e;case"keydown":case"keyup":$e=Hg;break;case"focusin":rt="focus",$e=dc;break;case"focusout":rt="blur",$e=dc;break;case"beforeblur":case"afterblur":$e=dc;break;case"click":if(a.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":$e=jd;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":$e=bg;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":$e=Wg;break;case dh:case hh:case ph:$e=Dg;break;case mh:$e=jg;break;case"scroll":$e=Rg;break;case"wheel":$e=Yg;break;case"copy":case"cut":case"paste":$e=Ig;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":$e=Yd}var st=(i&4)!==0,en=!st&&n==="scroll",te=st?Ce!==null?Ce+"Capture":null:Ce;st=[];for(var q=de,se;q!==null;){se=q;var ze=se.stateNode;if(se.tag===5&&ze!==null&&(se=ze,te!==null&&(ze=vt(q,te),ze!=null&&st.push(Eo(q,ze,se)))),en)break;q=q.return}0<st.length&&(Ce=new $e(Ce,rt,null,a,Pe),Fe.push({event:Ce,listeners:st}))}}if((i&7)===0){e:{if(Ce=n==="mouseover"||n==="pointerover",$e=n==="mouseout"||n==="pointerout",Ce&&a!==ht&&(rt=a.relatedTarget||a.fromElement)&&(Ir(rt)||rt[Pi]))break e;if(($e||Ce)&&(Ce=Pe.window===Pe?Pe:(Ce=Pe.ownerDocument)?Ce.defaultView||Ce.parentWindow:window,$e?(rt=a.relatedTarget||a.toElement,$e=de,rt=rt?Ir(rt):null,rt!==null&&(en=Wn(rt),rt!==en||rt.tag!==5&&rt.tag!==6)&&(rt=null)):($e=null,rt=de),$e!==rt)){if(st=jd,ze="onMouseLeave",te="onMouseEnter",q="mouse",(n==="pointerout"||n==="pointerover")&&(st=Yd,ze="onPointerLeave",te="onPointerEnter",q="pointer"),en=$e==null?Ce:vs($e),se=rt==null?Ce:vs(rt),Ce=new st(ze,q+"leave",$e,a,Pe),Ce.target=en,Ce.relatedTarget=se,ze=null,Ir(Pe)===de&&(st=new st(te,q+"enter",rt,a,Pe),st.target=se,st.relatedTarget=en,ze=st),en=ze,$e&&rt)t:{for(st=$e,te=rt,q=0,se=st;se;se=ms(se))q++;for(se=0,ze=te;ze;ze=ms(ze))se++;for(;0<q-se;)st=ms(st),q--;for(;0<se-q;)te=ms(te),se--;for(;q--;){if(st===te||te!==null&&st===te.alternate)break t;st=ms(st),te=ms(te)}st=null}else st=null;$e!==null&&Sh(Fe,Ce,$e,st,!1),rt!==null&&en!==null&&Sh(Fe,en,rt,st,!0)}}e:{if(Ce=de?vs(de):window,$e=Ce.nodeName&&Ce.nodeName.toLowerCase(),$e==="select"||$e==="input"&&Ce.type==="file")var ot=tv;else if(eh(Ce))if(nh)ot=sv;else{ot=iv;var pt=nv}else($e=Ce.nodeName)&&$e.toLowerCase()==="input"&&(Ce.type==="checkbox"||Ce.type==="radio")&&(ot=rv);if(ot&&(ot=ot(n,de))){th(Fe,ot,a,Pe);break e}pt&&pt(n,Ce,de),n==="focusout"&&(pt=Ce._wrapperState)&&pt.controlled&&Ce.type==="number"&&xe(Ce,"number",Ce.value)}switch(pt=de?vs(de):window,n){case"focusin":(eh(pt)||pt.contentEditable==="true")&&(hs=pt,_c=de,yo=null);break;case"focusout":yo=_c=hs=null;break;case"mousedown":xc=!0;break;case"contextmenu":case"mouseup":case"dragend":xc=!1,uh(Fe,a,Pe);break;case"selectionchange":if(lv)break;case"keydown":case"keyup":uh(Fe,a,Pe)}var mt;if(pc)e:{switch(n){case"compositionstart":var St="onCompositionStart";break e;case"compositionend":St="onCompositionEnd";break e;case"compositionupdate":St="onCompositionUpdate";break e}St=void 0}else ds?Jd(n,a)&&(St="onCompositionEnd"):n==="keydown"&&a.keyCode===229&&(St="onCompositionStart");St&&($d&&a.locale!=="ko"&&(ds||St!=="onCompositionStart"?St==="onCompositionEnd"&&ds&&(mt=Wd()):(rr=Pe,lc="value"in rr?rr.value:rr.textContent,ds=!0)),pt=Ea(de,St),0<pt.length&&(St=new qd(St,n,null,a,Pe),Fe.push({event:St,listeners:pt}),mt?St.data=mt:(mt=Qd(a),mt!==null&&(St.data=mt)))),(mt=Kg?Zg(n,a):Jg(n,a))&&(de=Ea(de,"onBeforeInput"),0<de.length&&(Pe=new qd("onBeforeInput","beforeinput",null,a,Pe),Fe.push({event:Pe,listeners:de}),Pe.data=mt))}xh(Fe,i)})}function Eo(n,i,a){return{instance:n,listener:i,currentTarget:a}}function Ea(n,i){for(var a=i+"Capture",c=[];n!==null;){var h=n,m=h.stateNode;h.tag===5&&m!==null&&(h=m,m=vt(n,a),m!=null&&c.unshift(Eo(n,m,h)),m=vt(n,i),m!=null&&c.push(Eo(n,m,h))),n=n.return}return c}function ms(n){if(n===null)return null;do n=n.return;while(n&&n.tag!==5);return n||null}function Sh(n,i,a,c,h){for(var m=i._reactName,E=[];a!==null&&a!==c;){var k=a,G=k.alternate,de=k.stateNode;if(G!==null&&G===c)break;k.tag===5&&de!==null&&(k=de,h?(G=vt(a,m),G!=null&&E.unshift(Eo(a,G,k))):h||(G=vt(a,m),G!=null&&E.push(Eo(a,G,k)))),a=a.return}E.length!==0&&n.push({event:i,listeners:E})}var dv=/\r\n?/g,hv=/\u0000|\uFFFD/g;function Mh(n){return(typeof n=="string"?n:""+n).replace(dv,`
`).replace(hv,"")}function wa(n,i,a){if(i=Mh(i),Mh(n)!==i&&a)throw Error(t(425))}function Ta(){}var Tc=null,Ac=null;function Rc(n,i){return n==="textarea"||n==="noscript"||typeof i.children=="string"||typeof i.children=="number"||typeof i.dangerouslySetInnerHTML=="object"&&i.dangerouslySetInnerHTML!==null&&i.dangerouslySetInnerHTML.__html!=null}var Cc=typeof setTimeout=="function"?setTimeout:void 0,pv=typeof clearTimeout=="function"?clearTimeout:void 0,Eh=typeof Promise=="function"?Promise:void 0,mv=typeof queueMicrotask=="function"?queueMicrotask:typeof Eh<"u"?function(n){return Eh.resolve(null).then(n).catch(gv)}:Cc;function gv(n){setTimeout(function(){throw n})}function bc(n,i){var a=i,c=0;do{var h=a.nextSibling;if(n.removeChild(a),h&&h.nodeType===8)if(a=h.data,a==="/$"){if(c===0){n.removeChild(h),ho(i);return}c--}else a!=="$"&&a!=="$?"&&a!=="$!"||c++;a=h}while(a);ho(i)}function or(n){for(;n!=null;n=n.nextSibling){var i=n.nodeType;if(i===1||i===3)break;if(i===8){if(i=n.data,i==="$"||i==="$!"||i==="$?")break;if(i==="/$")return null}}return n}function wh(n){n=n.previousSibling;for(var i=0;n;){if(n.nodeType===8){var a=n.data;if(a==="$"||a==="$!"||a==="$?"){if(i===0)return n;i--}else a==="/$"&&i++}n=n.previousSibling}return null}var gs=Math.random().toString(36).slice(2),_i="__reactFiber$"+gs,wo="__reactProps$"+gs,Pi="__reactContainer$"+gs,Pc="__reactEvents$"+gs,vv="__reactListeners$"+gs,_v="__reactHandles$"+gs;function Ir(n){var i=n[_i];if(i)return i;for(var a=n.parentNode;a;){if(i=a[Pi]||a[_i]){if(a=i.alternate,i.child!==null||a!==null&&a.child!==null)for(n=wh(n);n!==null;){if(a=n[_i])return a;n=wh(n)}return i}n=a,a=n.parentNode}return null}function To(n){return n=n[_i]||n[Pi],!n||n.tag!==5&&n.tag!==6&&n.tag!==13&&n.tag!==3?null:n}function vs(n){if(n.tag===5||n.tag===6)return n.stateNode;throw Error(t(33))}function Aa(n){return n[wo]||null}var Lc=[],_s=-1;function ar(n){return{current:n}}function Gt(n){0>_s||(n.current=Lc[_s],Lc[_s]=null,_s--)}function Ht(n,i){_s++,Lc[_s]=n.current,n.current=i}var lr={},Mn=ar(lr),Un=ar(!1),Ur=lr;function xs(n,i){var a=n.type.contextTypes;if(!a)return lr;var c=n.stateNode;if(c&&c.__reactInternalMemoizedUnmaskedChildContext===i)return c.__reactInternalMemoizedMaskedChildContext;var h={},m;for(m in a)h[m]=i[m];return c&&(n=n.stateNode,n.__reactInternalMemoizedUnmaskedChildContext=i,n.__reactInternalMemoizedMaskedChildContext=h),h}function Fn(n){return n=n.childContextTypes,n!=null}function Ra(){Gt(Un),Gt(Mn)}function Th(n,i,a){if(Mn.current!==lr)throw Error(t(168));Ht(Mn,i),Ht(Un,a)}function Ah(n,i,a){var c=n.stateNode;if(i=i.childContextTypes,typeof c.getChildContext!="function")return a;c=c.getChildContext();for(var h in c)if(!(h in i))throw Error(t(108,oe(n)||"Unknown",h));return ie({},a,c)}function Ca(n){return n=(n=n.stateNode)&&n.__reactInternalMemoizedMergedChildContext||lr,Ur=Mn.current,Ht(Mn,n),Ht(Un,Un.current),!0}function Rh(n,i,a){var c=n.stateNode;if(!c)throw Error(t(169));a?(n=Ah(n,i,Ur),c.__reactInternalMemoizedMergedChildContext=n,Gt(Un),Gt(Mn),Ht(Mn,n)):Gt(Un),Ht(Un,a)}var Li=null,ba=!1,Dc=!1;function Ch(n){Li===null?Li=[n]:Li.push(n)}function xv(n){ba=!0,Ch(n)}function cr(){if(!Dc&&Li!==null){Dc=!0;var n=0,i=Rt;try{var a=Li;for(Rt=1;n<a.length;n++){var c=a[n];do c=c(!0);while(c!==null)}Li=null,ba=!1}catch(h){throw Li!==null&&(Li=Li.slice(n+1)),b(We,cr),h}finally{Rt=i,Dc=!1}}return null}var ys=[],Ss=0,Pa=null,La=0,Zn=[],Jn=0,Fr=null,Di=1,Ni="";function Or(n,i){ys[Ss++]=La,ys[Ss++]=Pa,Pa=n,La=i}function bh(n,i,a){Zn[Jn++]=Di,Zn[Jn++]=Ni,Zn[Jn++]=Fr,Fr=n;var c=Di;n=Ni;var h=32-bt(c)-1;c&=~(1<<h),a+=1;var m=32-bt(i)+h;if(30<m){var E=h-h%5;m=(c&(1<<E)-1).toString(32),c>>=E,h-=E,Di=1<<32-bt(i)+h|a<<h|c,Ni=m+n}else Di=1<<m|a<<h|c,Ni=n}function Nc(n){n.return!==null&&(Or(n,1),bh(n,1,0))}function Ic(n){for(;n===Pa;)Pa=ys[--Ss],ys[Ss]=null,La=ys[--Ss],ys[Ss]=null;for(;n===Fr;)Fr=Zn[--Jn],Zn[Jn]=null,Ni=Zn[--Jn],Zn[Jn]=null,Di=Zn[--Jn],Zn[Jn]=null}var jn=null,qn=null,Xt=!1,ai=null;function Ph(n,i){var a=ni(5,null,null,0);a.elementType="DELETED",a.stateNode=i,a.return=n,i=n.deletions,i===null?(n.deletions=[a],n.flags|=16):i.push(a)}function Lh(n,i){switch(n.tag){case 5:var a=n.type;return i=i.nodeType!==1||a.toLowerCase()!==i.nodeName.toLowerCase()?null:i,i!==null?(n.stateNode=i,jn=n,qn=or(i.firstChild),!0):!1;case 6:return i=n.pendingProps===""||i.nodeType!==3?null:i,i!==null?(n.stateNode=i,jn=n,qn=null,!0):!1;case 13:return i=i.nodeType!==8?null:i,i!==null?(a=Fr!==null?{id:Di,overflow:Ni}:null,n.memoizedState={dehydrated:i,treeContext:a,retryLane:1073741824},a=ni(18,null,null,0),a.stateNode=i,a.return=n,n.child=a,jn=n,qn=null,!0):!1;default:return!1}}function Uc(n){return(n.mode&1)!==0&&(n.flags&128)===0}function Fc(n){if(Xt){var i=qn;if(i){var a=i;if(!Lh(n,i)){if(Uc(n))throw Error(t(418));i=or(a.nextSibling);var c=jn;i&&Lh(n,i)?Ph(c,a):(n.flags=n.flags&-4097|2,Xt=!1,jn=n)}}else{if(Uc(n))throw Error(t(418));n.flags=n.flags&-4097|2,Xt=!1,jn=n}}}function Dh(n){for(n=n.return;n!==null&&n.tag!==5&&n.tag!==3&&n.tag!==13;)n=n.return;jn=n}function Da(n){if(n!==jn)return!1;if(!Xt)return Dh(n),Xt=!0,!1;var i;if((i=n.tag!==3)&&!(i=n.tag!==5)&&(i=n.type,i=i!=="head"&&i!=="body"&&!Rc(n.type,n.memoizedProps)),i&&(i=qn)){if(Uc(n))throw Nh(),Error(t(418));for(;i;)Ph(n,i),i=or(i.nextSibling)}if(Dh(n),n.tag===13){if(n=n.memoizedState,n=n!==null?n.dehydrated:null,!n)throw Error(t(317));e:{for(n=n.nextSibling,i=0;n;){if(n.nodeType===8){var a=n.data;if(a==="/$"){if(i===0){qn=or(n.nextSibling);break e}i--}else a!=="$"&&a!=="$!"&&a!=="$?"||i++}n=n.nextSibling}qn=null}}else qn=jn?or(n.stateNode.nextSibling):null;return!0}function Nh(){for(var n=qn;n;)n=or(n.nextSibling)}function Ms(){qn=jn=null,Xt=!1}function Oc(n){ai===null?ai=[n]:ai.push(n)}var yv=R.ReactCurrentBatchConfig;function Ao(n,i,a){if(n=a.ref,n!==null&&typeof n!="function"&&typeof n!="object"){if(a._owner){if(a=a._owner,a){if(a.tag!==1)throw Error(t(309));var c=a.stateNode}if(!c)throw Error(t(147,n));var h=c,m=""+n;return i!==null&&i.ref!==null&&typeof i.ref=="function"&&i.ref._stringRef===m?i.ref:(i=function(E){var k=h.refs;E===null?delete k[m]:k[m]=E},i._stringRef=m,i)}if(typeof n!="string")throw Error(t(284));if(!a._owner)throw Error(t(290,n))}return n}function Na(n,i){throw n=Object.prototype.toString.call(i),Error(t(31,n==="[object Object]"?"object with keys {"+Object.keys(i).join(", ")+"}":n))}function Ih(n){var i=n._init;return i(n._payload)}function Uh(n){function i(te,q){if(n){var se=te.deletions;se===null?(te.deletions=[q],te.flags|=16):se.push(q)}}function a(te,q){if(!n)return null;for(;q!==null;)i(te,q),q=q.sibling;return null}function c(te,q){for(te=new Map;q!==null;)q.key!==null?te.set(q.key,q):te.set(q.index,q),q=q.sibling;return te}function h(te,q){return te=vr(te,q),te.index=0,te.sibling=null,te}function m(te,q,se){return te.index=se,n?(se=te.alternate,se!==null?(se=se.index,se<q?(te.flags|=2,q):se):(te.flags|=2,q)):(te.flags|=1048576,q)}function E(te){return n&&te.alternate===null&&(te.flags|=2),te}function k(te,q,se,ze){return q===null||q.tag!==6?(q=Cu(se,te.mode,ze),q.return=te,q):(q=h(q,se),q.return=te,q)}function G(te,q,se,ze){var ot=se.type;return ot===I?Pe(te,q,se.props.children,ze,se.key):q!==null&&(q.elementType===ot||typeof ot=="object"&&ot!==null&&ot.$$typeof===ce&&Ih(ot)===q.type)?(ze=h(q,se.props),ze.ref=Ao(te,q,se),ze.return=te,ze):(ze=il(se.type,se.key,se.props,null,te.mode,ze),ze.ref=Ao(te,q,se),ze.return=te,ze)}function de(te,q,se,ze){return q===null||q.tag!==4||q.stateNode.containerInfo!==se.containerInfo||q.stateNode.implementation!==se.implementation?(q=bu(se,te.mode,ze),q.return=te,q):(q=h(q,se.children||[]),q.return=te,q)}function Pe(te,q,se,ze,ot){return q===null||q.tag!==7?(q=Xr(se,te.mode,ze,ot),q.return=te,q):(q=h(q,se),q.return=te,q)}function Fe(te,q,se){if(typeof q=="string"&&q!==""||typeof q=="number")return q=Cu(""+q,te.mode,se),q.return=te,q;if(typeof q=="object"&&q!==null){switch(q.$$typeof){case z:return se=il(q.type,q.key,q.props,null,te.mode,se),se.ref=Ao(te,null,q),se.return=te,se;case H:return q=bu(q,te.mode,se),q.return=te,q;case ce:var ze=q._init;return Fe(te,ze(q._payload),se)}if(Re(q)||me(q))return q=Xr(q,te.mode,se,null),q.return=te,q;Na(te,q)}return null}function Ce(te,q,se,ze){var ot=q!==null?q.key:null;if(typeof se=="string"&&se!==""||typeof se=="number")return ot!==null?null:k(te,q,""+se,ze);if(typeof se=="object"&&se!==null){switch(se.$$typeof){case z:return se.key===ot?G(te,q,se,ze):null;case H:return se.key===ot?de(te,q,se,ze):null;case ce:return ot=se._init,Ce(te,q,ot(se._payload),ze)}if(Re(se)||me(se))return ot!==null?null:Pe(te,q,se,ze,null);Na(te,se)}return null}function $e(te,q,se,ze,ot){if(typeof ze=="string"&&ze!==""||typeof ze=="number")return te=te.get(se)||null,k(q,te,""+ze,ot);if(typeof ze=="object"&&ze!==null){switch(ze.$$typeof){case z:return te=te.get(ze.key===null?se:ze.key)||null,G(q,te,ze,ot);case H:return te=te.get(ze.key===null?se:ze.key)||null,de(q,te,ze,ot);case ce:var pt=ze._init;return $e(te,q,se,pt(ze._payload),ot)}if(Re(ze)||me(ze))return te=te.get(se)||null,Pe(q,te,ze,ot,null);Na(q,ze)}return null}function rt(te,q,se,ze){for(var ot=null,pt=null,mt=q,St=q=0,pn=null;mt!==null&&St<se.length;St++){mt.index>St?(pn=mt,mt=null):pn=mt.sibling;var Dt=Ce(te,mt,se[St],ze);if(Dt===null){mt===null&&(mt=pn);break}n&&mt&&Dt.alternate===null&&i(te,mt),q=m(Dt,q,St),pt===null?ot=Dt:pt.sibling=Dt,pt=Dt,mt=pn}if(St===se.length)return a(te,mt),Xt&&Or(te,St),ot;if(mt===null){for(;St<se.length;St++)mt=Fe(te,se[St],ze),mt!==null&&(q=m(mt,q,St),pt===null?ot=mt:pt.sibling=mt,pt=mt);return Xt&&Or(te,St),ot}for(mt=c(te,mt);St<se.length;St++)pn=$e(mt,te,St,se[St],ze),pn!==null&&(n&&pn.alternate!==null&&mt.delete(pn.key===null?St:pn.key),q=m(pn,q,St),pt===null?ot=pn:pt.sibling=pn,pt=pn);return n&&mt.forEach(function(_r){return i(te,_r)}),Xt&&Or(te,St),ot}function st(te,q,se,ze){var ot=me(se);if(typeof ot!="function")throw Error(t(150));if(se=ot.call(se),se==null)throw Error(t(151));for(var pt=ot=null,mt=q,St=q=0,pn=null,Dt=se.next();mt!==null&&!Dt.done;St++,Dt=se.next()){mt.index>St?(pn=mt,mt=null):pn=mt.sibling;var _r=Ce(te,mt,Dt.value,ze);if(_r===null){mt===null&&(mt=pn);break}n&&mt&&_r.alternate===null&&i(te,mt),q=m(_r,q,St),pt===null?ot=_r:pt.sibling=_r,pt=_r,mt=pn}if(Dt.done)return a(te,mt),Xt&&Or(te,St),ot;if(mt===null){for(;!Dt.done;St++,Dt=se.next())Dt=Fe(te,Dt.value,ze),Dt!==null&&(q=m(Dt,q,St),pt===null?ot=Dt:pt.sibling=Dt,pt=Dt);return Xt&&Or(te,St),ot}for(mt=c(te,mt);!Dt.done;St++,Dt=se.next())Dt=$e(mt,te,St,Dt.value,ze),Dt!==null&&(n&&Dt.alternate!==null&&mt.delete(Dt.key===null?St:Dt.key),q=m(Dt,q,St),pt===null?ot=Dt:pt.sibling=Dt,pt=Dt);return n&&mt.forEach(function(Qv){return i(te,Qv)}),Xt&&Or(te,St),ot}function en(te,q,se,ze){if(typeof se=="object"&&se!==null&&se.type===I&&se.key===null&&(se=se.props.children),typeof se=="object"&&se!==null){switch(se.$$typeof){case z:e:{for(var ot=se.key,pt=q;pt!==null;){if(pt.key===ot){if(ot=se.type,ot===I){if(pt.tag===7){a(te,pt.sibling),q=h(pt,se.props.children),q.return=te,te=q;break e}}else if(pt.elementType===ot||typeof ot=="object"&&ot!==null&&ot.$$typeof===ce&&Ih(ot)===pt.type){a(te,pt.sibling),q=h(pt,se.props),q.ref=Ao(te,pt,se),q.return=te,te=q;break e}a(te,pt);break}else i(te,pt);pt=pt.sibling}se.type===I?(q=Xr(se.props.children,te.mode,ze,se.key),q.return=te,te=q):(ze=il(se.type,se.key,se.props,null,te.mode,ze),ze.ref=Ao(te,q,se),ze.return=te,te=ze)}return E(te);case H:e:{for(pt=se.key;q!==null;){if(q.key===pt)if(q.tag===4&&q.stateNode.containerInfo===se.containerInfo&&q.stateNode.implementation===se.implementation){a(te,q.sibling),q=h(q,se.children||[]),q.return=te,te=q;break e}else{a(te,q);break}else i(te,q);q=q.sibling}q=bu(se,te.mode,ze),q.return=te,te=q}return E(te);case ce:return pt=se._init,en(te,q,pt(se._payload),ze)}if(Re(se))return rt(te,q,se,ze);if(me(se))return st(te,q,se,ze);Na(te,se)}return typeof se=="string"&&se!==""||typeof se=="number"?(se=""+se,q!==null&&q.tag===6?(a(te,q.sibling),q=h(q,se),q.return=te,te=q):(a(te,q),q=Cu(se,te.mode,ze),q.return=te,te=q),E(te)):a(te,q)}return en}var Es=Uh(!0),Fh=Uh(!1),Ia=ar(null),Ua=null,ws=null,kc=null;function Bc(){kc=ws=Ua=null}function zc(n){var i=Ia.current;Gt(Ia),n._currentValue=i}function Hc(n,i,a){for(;n!==null;){var c=n.alternate;if((n.childLanes&i)!==i?(n.childLanes|=i,c!==null&&(c.childLanes|=i)):c!==null&&(c.childLanes&i)!==i&&(c.childLanes|=i),n===a)break;n=n.return}}function Ts(n,i){Ua=n,kc=ws=null,n=n.dependencies,n!==null&&n.firstContext!==null&&((n.lanes&i)!==0&&(On=!0),n.firstContext=null)}function Qn(n){var i=n._currentValue;if(kc!==n)if(n={context:n,memoizedValue:i,next:null},ws===null){if(Ua===null)throw Error(t(308));ws=n,Ua.dependencies={lanes:0,firstContext:n}}else ws=ws.next=n;return i}var kr=null;function Vc(n){kr===null?kr=[n]:kr.push(n)}function Oh(n,i,a,c){var h=i.interleaved;return h===null?(a.next=a,Vc(i)):(a.next=h.next,h.next=a),i.interleaved=a,Ii(n,c)}function Ii(n,i){n.lanes|=i;var a=n.alternate;for(a!==null&&(a.lanes|=i),a=n,n=n.return;n!==null;)n.childLanes|=i,a=n.alternate,a!==null&&(a.childLanes|=i),a=n,n=n.return;return a.tag===3?a.stateNode:null}var ur=!1;function Gc(n){n.updateQueue={baseState:n.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,interleaved:null,lanes:0},effects:null}}function kh(n,i){n=n.updateQueue,i.updateQueue===n&&(i.updateQueue={baseState:n.baseState,firstBaseUpdate:n.firstBaseUpdate,lastBaseUpdate:n.lastBaseUpdate,shared:n.shared,effects:n.effects})}function Ui(n,i){return{eventTime:n,lane:i,tag:0,payload:null,callback:null,next:null}}function fr(n,i,a){var c=n.updateQueue;if(c===null)return null;if(c=c.shared,(Pt&2)!==0){var h=c.pending;return h===null?i.next=i:(i.next=h.next,h.next=i),c.pending=i,Ii(n,a)}return h=c.interleaved,h===null?(i.next=i,Vc(c)):(i.next=h.next,h.next=i),c.interleaved=i,Ii(n,a)}function Fa(n,i,a){if(i=i.updateQueue,i!==null&&(i=i.shared,(a&4194240)!==0)){var c=i.lanes;c&=n.pendingLanes,a|=c,i.lanes=a,Nr(n,a)}}function Bh(n,i){var a=n.updateQueue,c=n.alternate;if(c!==null&&(c=c.updateQueue,a===c)){var h=null,m=null;if(a=a.firstBaseUpdate,a!==null){do{var E={eventTime:a.eventTime,lane:a.lane,tag:a.tag,payload:a.payload,callback:a.callback,next:null};m===null?h=m=E:m=m.next=E,a=a.next}while(a!==null);m===null?h=m=i:m=m.next=i}else h=m=i;a={baseState:c.baseState,firstBaseUpdate:h,lastBaseUpdate:m,shared:c.shared,effects:c.effects},n.updateQueue=a;return}n=a.lastBaseUpdate,n===null?a.firstBaseUpdate=i:n.next=i,a.lastBaseUpdate=i}function Oa(n,i,a,c){var h=n.updateQueue;ur=!1;var m=h.firstBaseUpdate,E=h.lastBaseUpdate,k=h.shared.pending;if(k!==null){h.shared.pending=null;var G=k,de=G.next;G.next=null,E===null?m=de:E.next=de,E=G;var Pe=n.alternate;Pe!==null&&(Pe=Pe.updateQueue,k=Pe.lastBaseUpdate,k!==E&&(k===null?Pe.firstBaseUpdate=de:k.next=de,Pe.lastBaseUpdate=G))}if(m!==null){var Fe=h.baseState;E=0,Pe=de=G=null,k=m;do{var Ce=k.lane,$e=k.eventTime;if((c&Ce)===Ce){Pe!==null&&(Pe=Pe.next={eventTime:$e,lane:0,tag:k.tag,payload:k.payload,callback:k.callback,next:null});e:{var rt=n,st=k;switch(Ce=i,$e=a,st.tag){case 1:if(rt=st.payload,typeof rt=="function"){Fe=rt.call($e,Fe,Ce);break e}Fe=rt;break e;case 3:rt.flags=rt.flags&-65537|128;case 0:if(rt=st.payload,Ce=typeof rt=="function"?rt.call($e,Fe,Ce):rt,Ce==null)break e;Fe=ie({},Fe,Ce);break e;case 2:ur=!0}}k.callback!==null&&k.lane!==0&&(n.flags|=64,Ce=h.effects,Ce===null?h.effects=[k]:Ce.push(k))}else $e={eventTime:$e,lane:Ce,tag:k.tag,payload:k.payload,callback:k.callback,next:null},Pe===null?(de=Pe=$e,G=Fe):Pe=Pe.next=$e,E|=Ce;if(k=k.next,k===null){if(k=h.shared.pending,k===null)break;Ce=k,k=Ce.next,Ce.next=null,h.lastBaseUpdate=Ce,h.shared.pending=null}}while(!0);if(Pe===null&&(G=Fe),h.baseState=G,h.firstBaseUpdate=de,h.lastBaseUpdate=Pe,i=h.shared.interleaved,i!==null){h=i;do E|=h.lane,h=h.next;while(h!==i)}else m===null&&(h.shared.lanes=0);Hr|=E,n.lanes=E,n.memoizedState=Fe}}function zh(n,i,a){if(n=i.effects,i.effects=null,n!==null)for(i=0;i<n.length;i++){var c=n[i],h=c.callback;if(h!==null){if(c.callback=null,c=a,typeof h!="function")throw Error(t(191,h));h.call(c)}}}var Ro={},xi=ar(Ro),Co=ar(Ro),bo=ar(Ro);function Br(n){if(n===Ro)throw Error(t(174));return n}function Wc(n,i){switch(Ht(bo,i),Ht(Co,n),Ht(xi,Ro),n=i.nodeType,n){case 9:case 11:i=(i=i.documentElement)?i.namespaceURI:Ae(null,"");break;default:n=n===8?i.parentNode:i,i=n.namespaceURI||null,n=n.tagName,i=Ae(i,n)}Gt(xi),Ht(xi,i)}function As(){Gt(xi),Gt(Co),Gt(bo)}function Hh(n){Br(bo.current);var i=Br(xi.current),a=Ae(i,n.type);i!==a&&(Ht(Co,n),Ht(xi,a))}function Xc(n){Co.current===n&&(Gt(xi),Gt(Co))}var jt=ar(0);function ka(n){for(var i=n;i!==null;){if(i.tag===13){var a=i.memoizedState;if(a!==null&&(a=a.dehydrated,a===null||a.data==="$?"||a.data==="$!"))return i}else if(i.tag===19&&i.memoizedProps.revealOrder!==void 0){if((i.flags&128)!==0)return i}else if(i.child!==null){i.child.return=i,i=i.child;continue}if(i===n)break;for(;i.sibling===null;){if(i.return===null||i.return===n)return null;i=i.return}i.sibling.return=i.return,i=i.sibling}return null}var jc=[];function qc(){for(var n=0;n<jc.length;n++)jc[n]._workInProgressVersionPrimary=null;jc.length=0}var Ba=R.ReactCurrentDispatcher,Yc=R.ReactCurrentBatchConfig,zr=0,qt=null,sn=null,dn=null,za=!1,Po=!1,Lo=0,Sv=0;function En(){throw Error(t(321))}function $c(n,i){if(i===null)return!1;for(var a=0;a<i.length&&a<n.length;a++)if(!oi(n[a],i[a]))return!1;return!0}function Kc(n,i,a,c,h,m){if(zr=m,qt=i,i.memoizedState=null,i.updateQueue=null,i.lanes=0,Ba.current=n===null||n.memoizedState===null?Tv:Av,n=a(c,h),Po){m=0;do{if(Po=!1,Lo=0,25<=m)throw Error(t(301));m+=1,dn=sn=null,i.updateQueue=null,Ba.current=Rv,n=a(c,h)}while(Po)}if(Ba.current=Ga,i=sn!==null&&sn.next!==null,zr=0,dn=sn=qt=null,za=!1,i)throw Error(t(300));return n}function Zc(){var n=Lo!==0;return Lo=0,n}function yi(){var n={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return dn===null?qt.memoizedState=dn=n:dn=dn.next=n,dn}function ei(){if(sn===null){var n=qt.alternate;n=n!==null?n.memoizedState:null}else n=sn.next;var i=dn===null?qt.memoizedState:dn.next;if(i!==null)dn=i,sn=n;else{if(n===null)throw Error(t(310));sn=n,n={memoizedState:sn.memoizedState,baseState:sn.baseState,baseQueue:sn.baseQueue,queue:sn.queue,next:null},dn===null?qt.memoizedState=dn=n:dn=dn.next=n}return dn}function Do(n,i){return typeof i=="function"?i(n):i}function Jc(n){var i=ei(),a=i.queue;if(a===null)throw Error(t(311));a.lastRenderedReducer=n;var c=sn,h=c.baseQueue,m=a.pending;if(m!==null){if(h!==null){var E=h.next;h.next=m.next,m.next=E}c.baseQueue=h=m,a.pending=null}if(h!==null){m=h.next,c=c.baseState;var k=E=null,G=null,de=m;do{var Pe=de.lane;if((zr&Pe)===Pe)G!==null&&(G=G.next={lane:0,action:de.action,hasEagerState:de.hasEagerState,eagerState:de.eagerState,next:null}),c=de.hasEagerState?de.eagerState:n(c,de.action);else{var Fe={lane:Pe,action:de.action,hasEagerState:de.hasEagerState,eagerState:de.eagerState,next:null};G===null?(k=G=Fe,E=c):G=G.next=Fe,qt.lanes|=Pe,Hr|=Pe}de=de.next}while(de!==null&&de!==m);G===null?E=c:G.next=k,oi(c,i.memoizedState)||(On=!0),i.memoizedState=c,i.baseState=E,i.baseQueue=G,a.lastRenderedState=c}if(n=a.interleaved,n!==null){h=n;do m=h.lane,qt.lanes|=m,Hr|=m,h=h.next;while(h!==n)}else h===null&&(a.lanes=0);return[i.memoizedState,a.dispatch]}function Qc(n){var i=ei(),a=i.queue;if(a===null)throw Error(t(311));a.lastRenderedReducer=n;var c=a.dispatch,h=a.pending,m=i.memoizedState;if(h!==null){a.pending=null;var E=h=h.next;do m=n(m,E.action),E=E.next;while(E!==h);oi(m,i.memoizedState)||(On=!0),i.memoizedState=m,i.baseQueue===null&&(i.baseState=m),a.lastRenderedState=m}return[m,c]}function Vh(){}function Gh(n,i){var a=qt,c=ei(),h=i(),m=!oi(c.memoizedState,h);if(m&&(c.memoizedState=h,On=!0),c=c.queue,eu(jh.bind(null,a,c,n),[n]),c.getSnapshot!==i||m||dn!==null&&dn.memoizedState.tag&1){if(a.flags|=2048,No(9,Xh.bind(null,a,c,h,i),void 0,null),hn===null)throw Error(t(349));(zr&30)!==0||Wh(a,i,h)}return h}function Wh(n,i,a){n.flags|=16384,n={getSnapshot:i,value:a},i=qt.updateQueue,i===null?(i={lastEffect:null,stores:null},qt.updateQueue=i,i.stores=[n]):(a=i.stores,a===null?i.stores=[n]:a.push(n))}function Xh(n,i,a,c){i.value=a,i.getSnapshot=c,qh(i)&&Yh(n)}function jh(n,i,a){return a(function(){qh(i)&&Yh(n)})}function qh(n){var i=n.getSnapshot;n=n.value;try{var a=i();return!oi(n,a)}catch{return!0}}function Yh(n){var i=Ii(n,1);i!==null&&fi(i,n,1,-1)}function $h(n){var i=yi();return typeof n=="function"&&(n=n()),i.memoizedState=i.baseState=n,n={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:Do,lastRenderedState:n},i.queue=n,n=n.dispatch=wv.bind(null,qt,n),[i.memoizedState,n]}function No(n,i,a,c){return n={tag:n,create:i,destroy:a,deps:c,next:null},i=qt.updateQueue,i===null?(i={lastEffect:null,stores:null},qt.updateQueue=i,i.lastEffect=n.next=n):(a=i.lastEffect,a===null?i.lastEffect=n.next=n:(c=a.next,a.next=n,n.next=c,i.lastEffect=n)),n}function Kh(){return ei().memoizedState}function Ha(n,i,a,c){var h=yi();qt.flags|=n,h.memoizedState=No(1|i,a,void 0,c===void 0?null:c)}function Va(n,i,a,c){var h=ei();c=c===void 0?null:c;var m=void 0;if(sn!==null){var E=sn.memoizedState;if(m=E.destroy,c!==null&&$c(c,E.deps)){h.memoizedState=No(i,a,m,c);return}}qt.flags|=n,h.memoizedState=No(1|i,a,m,c)}function Zh(n,i){return Ha(8390656,8,n,i)}function eu(n,i){return Va(2048,8,n,i)}function Jh(n,i){return Va(4,2,n,i)}function Qh(n,i){return Va(4,4,n,i)}function ep(n,i){if(typeof i=="function")return n=n(),i(n),function(){i(null)};if(i!=null)return n=n(),i.current=n,function(){i.current=null}}function tp(n,i,a){return a=a!=null?a.concat([n]):null,Va(4,4,ep.bind(null,i,n),a)}function tu(){}function np(n,i){var a=ei();i=i===void 0?null:i;var c=a.memoizedState;return c!==null&&i!==null&&$c(i,c[1])?c[0]:(a.memoizedState=[n,i],n)}function ip(n,i){var a=ei();i=i===void 0?null:i;var c=a.memoizedState;return c!==null&&i!==null&&$c(i,c[1])?c[0]:(n=n(),a.memoizedState=[n,i],n)}function rp(n,i,a){return(zr&21)===0?(n.baseState&&(n.baseState=!1,On=!0),n.memoizedState=a):(oi(a,i)||(a=bn(),qt.lanes|=a,Hr|=a,n.baseState=!0),i)}function Mv(n,i){var a=Rt;Rt=a!==0&&4>a?a:4,n(!0);var c=Yc.transition;Yc.transition={};try{n(!1),i()}finally{Rt=a,Yc.transition=c}}function sp(){return ei().memoizedState}function Ev(n,i,a){var c=mr(n);if(a={lane:c,action:a,hasEagerState:!1,eagerState:null,next:null},op(n))ap(i,a);else if(a=Oh(n,i,a,c),a!==null){var h=Ln();fi(a,n,c,h),lp(a,i,c)}}function wv(n,i,a){var c=mr(n),h={lane:c,action:a,hasEagerState:!1,eagerState:null,next:null};if(op(n))ap(i,h);else{var m=n.alternate;if(n.lanes===0&&(m===null||m.lanes===0)&&(m=i.lastRenderedReducer,m!==null))try{var E=i.lastRenderedState,k=m(E,a);if(h.hasEagerState=!0,h.eagerState=k,oi(k,E)){var G=i.interleaved;G===null?(h.next=h,Vc(i)):(h.next=G.next,G.next=h),i.interleaved=h;return}}catch{}finally{}a=Oh(n,i,h,c),a!==null&&(h=Ln(),fi(a,n,c,h),lp(a,i,c))}}function op(n){var i=n.alternate;return n===qt||i!==null&&i===qt}function ap(n,i){Po=za=!0;var a=n.pending;a===null?i.next=i:(i.next=a.next,a.next=i),n.pending=i}function lp(n,i,a){if((a&4194240)!==0){var c=i.lanes;c&=n.pendingLanes,a|=c,i.lanes=a,Nr(n,a)}}var Ga={readContext:Qn,useCallback:En,useContext:En,useEffect:En,useImperativeHandle:En,useInsertionEffect:En,useLayoutEffect:En,useMemo:En,useReducer:En,useRef:En,useState:En,useDebugValue:En,useDeferredValue:En,useTransition:En,useMutableSource:En,useSyncExternalStore:En,useId:En,unstable_isNewReconciler:!1},Tv={readContext:Qn,useCallback:function(n,i){return yi().memoizedState=[n,i===void 0?null:i],n},useContext:Qn,useEffect:Zh,useImperativeHandle:function(n,i,a){return a=a!=null?a.concat([n]):null,Ha(4194308,4,ep.bind(null,i,n),a)},useLayoutEffect:function(n,i){return Ha(4194308,4,n,i)},useInsertionEffect:function(n,i){return Ha(4,2,n,i)},useMemo:function(n,i){var a=yi();return i=i===void 0?null:i,n=n(),a.memoizedState=[n,i],n},useReducer:function(n,i,a){var c=yi();return i=a!==void 0?a(i):i,c.memoizedState=c.baseState=i,n={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:n,lastRenderedState:i},c.queue=n,n=n.dispatch=Ev.bind(null,qt,n),[c.memoizedState,n]},useRef:function(n){var i=yi();return n={current:n},i.memoizedState=n},useState:$h,useDebugValue:tu,useDeferredValue:function(n){return yi().memoizedState=n},useTransition:function(){var n=$h(!1),i=n[0];return n=Mv.bind(null,n[1]),yi().memoizedState=n,[i,n]},useMutableSource:function(){},useSyncExternalStore:function(n,i,a){var c=qt,h=yi();if(Xt){if(a===void 0)throw Error(t(407));a=a()}else{if(a=i(),hn===null)throw Error(t(349));(zr&30)!==0||Wh(c,i,a)}h.memoizedState=a;var m={value:a,getSnapshot:i};return h.queue=m,Zh(jh.bind(null,c,m,n),[n]),c.flags|=2048,No(9,Xh.bind(null,c,m,a,i),void 0,null),a},useId:function(){var n=yi(),i=hn.identifierPrefix;if(Xt){var a=Ni,c=Di;a=(c&~(1<<32-bt(c)-1)).toString(32)+a,i=":"+i+"R"+a,a=Lo++,0<a&&(i+="H"+a.toString(32)),i+=":"}else a=Sv++,i=":"+i+"r"+a.toString(32)+":";return n.memoizedState=i},unstable_isNewReconciler:!1},Av={readContext:Qn,useCallback:np,useContext:Qn,useEffect:eu,useImperativeHandle:tp,useInsertionEffect:Jh,useLayoutEffect:Qh,useMemo:ip,useReducer:Jc,useRef:Kh,useState:function(){return Jc(Do)},useDebugValue:tu,useDeferredValue:function(n){var i=ei();return rp(i,sn.memoizedState,n)},useTransition:function(){var n=Jc(Do)[0],i=ei().memoizedState;return[n,i]},useMutableSource:Vh,useSyncExternalStore:Gh,useId:sp,unstable_isNewReconciler:!1},Rv={readContext:Qn,useCallback:np,useContext:Qn,useEffect:eu,useImperativeHandle:tp,useInsertionEffect:Jh,useLayoutEffect:Qh,useMemo:ip,useReducer:Qc,useRef:Kh,useState:function(){return Qc(Do)},useDebugValue:tu,useDeferredValue:function(n){var i=ei();return sn===null?i.memoizedState=n:rp(i,sn.memoizedState,n)},useTransition:function(){var n=Qc(Do)[0],i=ei().memoizedState;return[n,i]},useMutableSource:Vh,useSyncExternalStore:Gh,useId:sp,unstable_isNewReconciler:!1};function li(n,i){if(n&&n.defaultProps){i=ie({},i),n=n.defaultProps;for(var a in n)i[a]===void 0&&(i[a]=n[a]);return i}return i}function nu(n,i,a,c){i=n.memoizedState,a=a(c,i),a=a==null?i:ie({},i,a),n.memoizedState=a,n.lanes===0&&(n.updateQueue.baseState=a)}var Wa={isMounted:function(n){return(n=n._reactInternals)?Wn(n)===n:!1},enqueueSetState:function(n,i,a){n=n._reactInternals;var c=Ln(),h=mr(n),m=Ui(c,h);m.payload=i,a!=null&&(m.callback=a),i=fr(n,m,h),i!==null&&(fi(i,n,h,c),Fa(i,n,h))},enqueueReplaceState:function(n,i,a){n=n._reactInternals;var c=Ln(),h=mr(n),m=Ui(c,h);m.tag=1,m.payload=i,a!=null&&(m.callback=a),i=fr(n,m,h),i!==null&&(fi(i,n,h,c),Fa(i,n,h))},enqueueForceUpdate:function(n,i){n=n._reactInternals;var a=Ln(),c=mr(n),h=Ui(a,c);h.tag=2,i!=null&&(h.callback=i),i=fr(n,h,c),i!==null&&(fi(i,n,c,a),Fa(i,n,c))}};function cp(n,i,a,c,h,m,E){return n=n.stateNode,typeof n.shouldComponentUpdate=="function"?n.shouldComponentUpdate(c,m,E):i.prototype&&i.prototype.isPureReactComponent?!xo(a,c)||!xo(h,m):!0}function up(n,i,a){var c=!1,h=lr,m=i.contextType;return typeof m=="object"&&m!==null?m=Qn(m):(h=Fn(i)?Ur:Mn.current,c=i.contextTypes,m=(c=c!=null)?xs(n,h):lr),i=new i(a,m),n.memoizedState=i.state!==null&&i.state!==void 0?i.state:null,i.updater=Wa,n.stateNode=i,i._reactInternals=n,c&&(n=n.stateNode,n.__reactInternalMemoizedUnmaskedChildContext=h,n.__reactInternalMemoizedMaskedChildContext=m),i}function fp(n,i,a,c){n=i.state,typeof i.componentWillReceiveProps=="function"&&i.componentWillReceiveProps(a,c),typeof i.UNSAFE_componentWillReceiveProps=="function"&&i.UNSAFE_componentWillReceiveProps(a,c),i.state!==n&&Wa.enqueueReplaceState(i,i.state,null)}function iu(n,i,a,c){var h=n.stateNode;h.props=a,h.state=n.memoizedState,h.refs={},Gc(n);var m=i.contextType;typeof m=="object"&&m!==null?h.context=Qn(m):(m=Fn(i)?Ur:Mn.current,h.context=xs(n,m)),h.state=n.memoizedState,m=i.getDerivedStateFromProps,typeof m=="function"&&(nu(n,i,m,a),h.state=n.memoizedState),typeof i.getDerivedStateFromProps=="function"||typeof h.getSnapshotBeforeUpdate=="function"||typeof h.UNSAFE_componentWillMount!="function"&&typeof h.componentWillMount!="function"||(i=h.state,typeof h.componentWillMount=="function"&&h.componentWillMount(),typeof h.UNSAFE_componentWillMount=="function"&&h.UNSAFE_componentWillMount(),i!==h.state&&Wa.enqueueReplaceState(h,h.state,null),Oa(n,a,h,c),h.state=n.memoizedState),typeof h.componentDidMount=="function"&&(n.flags|=4194308)}function Rs(n,i){try{var a="",c=i;do a+=he(c),c=c.return;while(c);var h=a}catch(m){h=`
Error generating stack: `+m.message+`
`+m.stack}return{value:n,source:i,stack:h,digest:null}}function ru(n,i,a){return{value:n,source:null,stack:a??null,digest:i??null}}function su(n,i){try{console.error(i.value)}catch(a){setTimeout(function(){throw a})}}var Cv=typeof WeakMap=="function"?WeakMap:Map;function dp(n,i,a){a=Ui(-1,a),a.tag=3,a.payload={element:null};var c=i.value;return a.callback=function(){Za||(Za=!0,yu=c),su(n,i)},a}function hp(n,i,a){a=Ui(-1,a),a.tag=3;var c=n.type.getDerivedStateFromError;if(typeof c=="function"){var h=i.value;a.payload=function(){return c(h)},a.callback=function(){su(n,i)}}var m=n.stateNode;return m!==null&&typeof m.componentDidCatch=="function"&&(a.callback=function(){su(n,i),typeof c!="function"&&(hr===null?hr=new Set([this]):hr.add(this));var E=i.stack;this.componentDidCatch(i.value,{componentStack:E!==null?E:""})}),a}function pp(n,i,a){var c=n.pingCache;if(c===null){c=n.pingCache=new Cv;var h=new Set;c.set(i,h)}else h=c.get(i),h===void 0&&(h=new Set,c.set(i,h));h.has(a)||(h.add(a),n=Vv.bind(null,n,i,a),i.then(n,n))}function mp(n){do{var i;if((i=n.tag===13)&&(i=n.memoizedState,i=i!==null?i.dehydrated!==null:!0),i)return n;n=n.return}while(n!==null);return null}function gp(n,i,a,c,h){return(n.mode&1)===0?(n===i?n.flags|=65536:(n.flags|=128,a.flags|=131072,a.flags&=-52805,a.tag===1&&(a.alternate===null?a.tag=17:(i=Ui(-1,1),i.tag=2,fr(a,i,1))),a.lanes|=1),n):(n.flags|=65536,n.lanes=h,n)}var bv=R.ReactCurrentOwner,On=!1;function Pn(n,i,a,c){i.child=n===null?Fh(i,null,a,c):Es(i,n.child,a,c)}function vp(n,i,a,c,h){a=a.render;var m=i.ref;return Ts(i,h),c=Kc(n,i,a,c,m,h),a=Zc(),n!==null&&!On?(i.updateQueue=n.updateQueue,i.flags&=-2053,n.lanes&=~h,Fi(n,i,h)):(Xt&&a&&Nc(i),i.flags|=1,Pn(n,i,c,h),i.child)}function _p(n,i,a,c,h){if(n===null){var m=a.type;return typeof m=="function"&&!Ru(m)&&m.defaultProps===void 0&&a.compare===null&&a.defaultProps===void 0?(i.tag=15,i.type=m,xp(n,i,m,c,h)):(n=il(a.type,null,c,i,i.mode,h),n.ref=i.ref,n.return=i,i.child=n)}if(m=n.child,(n.lanes&h)===0){var E=m.memoizedProps;if(a=a.compare,a=a!==null?a:xo,a(E,c)&&n.ref===i.ref)return Fi(n,i,h)}return i.flags|=1,n=vr(m,c),n.ref=i.ref,n.return=i,i.child=n}function xp(n,i,a,c,h){if(n!==null){var m=n.memoizedProps;if(xo(m,c)&&n.ref===i.ref)if(On=!1,i.pendingProps=c=m,(n.lanes&h)!==0)(n.flags&131072)!==0&&(On=!0);else return i.lanes=n.lanes,Fi(n,i,h)}return ou(n,i,a,c,h)}function yp(n,i,a){var c=i.pendingProps,h=c.children,m=n!==null?n.memoizedState:null;if(c.mode==="hidden")if((i.mode&1)===0)i.memoizedState={baseLanes:0,cachePool:null,transitions:null},Ht(bs,Yn),Yn|=a;else{if((a&1073741824)===0)return n=m!==null?m.baseLanes|a:a,i.lanes=i.childLanes=1073741824,i.memoizedState={baseLanes:n,cachePool:null,transitions:null},i.updateQueue=null,Ht(bs,Yn),Yn|=n,null;i.memoizedState={baseLanes:0,cachePool:null,transitions:null},c=m!==null?m.baseLanes:a,Ht(bs,Yn),Yn|=c}else m!==null?(c=m.baseLanes|a,i.memoizedState=null):c=a,Ht(bs,Yn),Yn|=c;return Pn(n,i,h,a),i.child}function Sp(n,i){var a=i.ref;(n===null&&a!==null||n!==null&&n.ref!==a)&&(i.flags|=512,i.flags|=2097152)}function ou(n,i,a,c,h){var m=Fn(a)?Ur:Mn.current;return m=xs(i,m),Ts(i,h),a=Kc(n,i,a,c,m,h),c=Zc(),n!==null&&!On?(i.updateQueue=n.updateQueue,i.flags&=-2053,n.lanes&=~h,Fi(n,i,h)):(Xt&&c&&Nc(i),i.flags|=1,Pn(n,i,a,h),i.child)}function Mp(n,i,a,c,h){if(Fn(a)){var m=!0;Ca(i)}else m=!1;if(Ts(i,h),i.stateNode===null)ja(n,i),up(i,a,c),iu(i,a,c,h),c=!0;else if(n===null){var E=i.stateNode,k=i.memoizedProps;E.props=k;var G=E.context,de=a.contextType;typeof de=="object"&&de!==null?de=Qn(de):(de=Fn(a)?Ur:Mn.current,de=xs(i,de));var Pe=a.getDerivedStateFromProps,Fe=typeof Pe=="function"||typeof E.getSnapshotBeforeUpdate=="function";Fe||typeof E.UNSAFE_componentWillReceiveProps!="function"&&typeof E.componentWillReceiveProps!="function"||(k!==c||G!==de)&&fp(i,E,c,de),ur=!1;var Ce=i.memoizedState;E.state=Ce,Oa(i,c,E,h),G=i.memoizedState,k!==c||Ce!==G||Un.current||ur?(typeof Pe=="function"&&(nu(i,a,Pe,c),G=i.memoizedState),(k=ur||cp(i,a,k,c,Ce,G,de))?(Fe||typeof E.UNSAFE_componentWillMount!="function"&&typeof E.componentWillMount!="function"||(typeof E.componentWillMount=="function"&&E.componentWillMount(),typeof E.UNSAFE_componentWillMount=="function"&&E.UNSAFE_componentWillMount()),typeof E.componentDidMount=="function"&&(i.flags|=4194308)):(typeof E.componentDidMount=="function"&&(i.flags|=4194308),i.memoizedProps=c,i.memoizedState=G),E.props=c,E.state=G,E.context=de,c=k):(typeof E.componentDidMount=="function"&&(i.flags|=4194308),c=!1)}else{E=i.stateNode,kh(n,i),k=i.memoizedProps,de=i.type===i.elementType?k:li(i.type,k),E.props=de,Fe=i.pendingProps,Ce=E.context,G=a.contextType,typeof G=="object"&&G!==null?G=Qn(G):(G=Fn(a)?Ur:Mn.current,G=xs(i,G));var $e=a.getDerivedStateFromProps;(Pe=typeof $e=="function"||typeof E.getSnapshotBeforeUpdate=="function")||typeof E.UNSAFE_componentWillReceiveProps!="function"&&typeof E.componentWillReceiveProps!="function"||(k!==Fe||Ce!==G)&&fp(i,E,c,G),ur=!1,Ce=i.memoizedState,E.state=Ce,Oa(i,c,E,h);var rt=i.memoizedState;k!==Fe||Ce!==rt||Un.current||ur?(typeof $e=="function"&&(nu(i,a,$e,c),rt=i.memoizedState),(de=ur||cp(i,a,de,c,Ce,rt,G)||!1)?(Pe||typeof E.UNSAFE_componentWillUpdate!="function"&&typeof E.componentWillUpdate!="function"||(typeof E.componentWillUpdate=="function"&&E.componentWillUpdate(c,rt,G),typeof E.UNSAFE_componentWillUpdate=="function"&&E.UNSAFE_componentWillUpdate(c,rt,G)),typeof E.componentDidUpdate=="function"&&(i.flags|=4),typeof E.getSnapshotBeforeUpdate=="function"&&(i.flags|=1024)):(typeof E.componentDidUpdate!="function"||k===n.memoizedProps&&Ce===n.memoizedState||(i.flags|=4),typeof E.getSnapshotBeforeUpdate!="function"||k===n.memoizedProps&&Ce===n.memoizedState||(i.flags|=1024),i.memoizedProps=c,i.memoizedState=rt),E.props=c,E.state=rt,E.context=G,c=de):(typeof E.componentDidUpdate!="function"||k===n.memoizedProps&&Ce===n.memoizedState||(i.flags|=4),typeof E.getSnapshotBeforeUpdate!="function"||k===n.memoizedProps&&Ce===n.memoizedState||(i.flags|=1024),c=!1)}return au(n,i,a,c,m,h)}function au(n,i,a,c,h,m){Sp(n,i);var E=(i.flags&128)!==0;if(!c&&!E)return h&&Rh(i,a,!1),Fi(n,i,m);c=i.stateNode,bv.current=i;var k=E&&typeof a.getDerivedStateFromError!="function"?null:c.render();return i.flags|=1,n!==null&&E?(i.child=Es(i,n.child,null,m),i.child=Es(i,null,k,m)):Pn(n,i,k,m),i.memoizedState=c.state,h&&Rh(i,a,!0),i.child}function Ep(n){var i=n.stateNode;i.pendingContext?Th(n,i.pendingContext,i.pendingContext!==i.context):i.context&&Th(n,i.context,!1),Wc(n,i.containerInfo)}function wp(n,i,a,c,h){return Ms(),Oc(h),i.flags|=256,Pn(n,i,a,c),i.child}var lu={dehydrated:null,treeContext:null,retryLane:0};function cu(n){return{baseLanes:n,cachePool:null,transitions:null}}function Tp(n,i,a){var c=i.pendingProps,h=jt.current,m=!1,E=(i.flags&128)!==0,k;if((k=E)||(k=n!==null&&n.memoizedState===null?!1:(h&2)!==0),k?(m=!0,i.flags&=-129):(n===null||n.memoizedState!==null)&&(h|=1),Ht(jt,h&1),n===null)return Fc(i),n=i.memoizedState,n!==null&&(n=n.dehydrated,n!==null)?((i.mode&1)===0?i.lanes=1:n.data==="$!"?i.lanes=8:i.lanes=1073741824,null):(E=c.children,n=c.fallback,m?(c=i.mode,m=i.child,E={mode:"hidden",children:E},(c&1)===0&&m!==null?(m.childLanes=0,m.pendingProps=E):m=rl(E,c,0,null),n=Xr(n,c,a,null),m.return=i,n.return=i,m.sibling=n,i.child=m,i.child.memoizedState=cu(a),i.memoizedState=lu,n):uu(i,E));if(h=n.memoizedState,h!==null&&(k=h.dehydrated,k!==null))return Pv(n,i,E,c,k,h,a);if(m){m=c.fallback,E=i.mode,h=n.child,k=h.sibling;var G={mode:"hidden",children:c.children};return(E&1)===0&&i.child!==h?(c=i.child,c.childLanes=0,c.pendingProps=G,i.deletions=null):(c=vr(h,G),c.subtreeFlags=h.subtreeFlags&14680064),k!==null?m=vr(k,m):(m=Xr(m,E,a,null),m.flags|=2),m.return=i,c.return=i,c.sibling=m,i.child=c,c=m,m=i.child,E=n.child.memoizedState,E=E===null?cu(a):{baseLanes:E.baseLanes|a,cachePool:null,transitions:E.transitions},m.memoizedState=E,m.childLanes=n.childLanes&~a,i.memoizedState=lu,c}return m=n.child,n=m.sibling,c=vr(m,{mode:"visible",children:c.children}),(i.mode&1)===0&&(c.lanes=a),c.return=i,c.sibling=null,n!==null&&(a=i.deletions,a===null?(i.deletions=[n],i.flags|=16):a.push(n)),i.child=c,i.memoizedState=null,c}function uu(n,i){return i=rl({mode:"visible",children:i},n.mode,0,null),i.return=n,n.child=i}function Xa(n,i,a,c){return c!==null&&Oc(c),Es(i,n.child,null,a),n=uu(i,i.pendingProps.children),n.flags|=2,i.memoizedState=null,n}function Pv(n,i,a,c,h,m,E){if(a)return i.flags&256?(i.flags&=-257,c=ru(Error(t(422))),Xa(n,i,E,c)):i.memoizedState!==null?(i.child=n.child,i.flags|=128,null):(m=c.fallback,h=i.mode,c=rl({mode:"visible",children:c.children},h,0,null),m=Xr(m,h,E,null),m.flags|=2,c.return=i,m.return=i,c.sibling=m,i.child=c,(i.mode&1)!==0&&Es(i,n.child,null,E),i.child.memoizedState=cu(E),i.memoizedState=lu,m);if((i.mode&1)===0)return Xa(n,i,E,null);if(h.data==="$!"){if(c=h.nextSibling&&h.nextSibling.dataset,c)var k=c.dgst;return c=k,m=Error(t(419)),c=ru(m,c,void 0),Xa(n,i,E,c)}if(k=(E&n.childLanes)!==0,On||k){if(c=hn,c!==null){switch(E&-E){case 4:h=2;break;case 16:h=8;break;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:h=32;break;case 536870912:h=268435456;break;default:h=0}h=(h&(c.suspendedLanes|E))!==0?0:h,h!==0&&h!==m.retryLane&&(m.retryLane=h,Ii(n,h),fi(c,n,h,-1))}return Au(),c=ru(Error(t(421))),Xa(n,i,E,c)}return h.data==="$?"?(i.flags|=128,i.child=n.child,i=Gv.bind(null,n),h._reactRetry=i,null):(n=m.treeContext,qn=or(h.nextSibling),jn=i,Xt=!0,ai=null,n!==null&&(Zn[Jn++]=Di,Zn[Jn++]=Ni,Zn[Jn++]=Fr,Di=n.id,Ni=n.overflow,Fr=i),i=uu(i,c.children),i.flags|=4096,i)}function Ap(n,i,a){n.lanes|=i;var c=n.alternate;c!==null&&(c.lanes|=i),Hc(n.return,i,a)}function fu(n,i,a,c,h){var m=n.memoizedState;m===null?n.memoizedState={isBackwards:i,rendering:null,renderingStartTime:0,last:c,tail:a,tailMode:h}:(m.isBackwards=i,m.rendering=null,m.renderingStartTime=0,m.last=c,m.tail=a,m.tailMode=h)}function Rp(n,i,a){var c=i.pendingProps,h=c.revealOrder,m=c.tail;if(Pn(n,i,c.children,a),c=jt.current,(c&2)!==0)c=c&1|2,i.flags|=128;else{if(n!==null&&(n.flags&128)!==0)e:for(n=i.child;n!==null;){if(n.tag===13)n.memoizedState!==null&&Ap(n,a,i);else if(n.tag===19)Ap(n,a,i);else if(n.child!==null){n.child.return=n,n=n.child;continue}if(n===i)break e;for(;n.sibling===null;){if(n.return===null||n.return===i)break e;n=n.return}n.sibling.return=n.return,n=n.sibling}c&=1}if(Ht(jt,c),(i.mode&1)===0)i.memoizedState=null;else switch(h){case"forwards":for(a=i.child,h=null;a!==null;)n=a.alternate,n!==null&&ka(n)===null&&(h=a),a=a.sibling;a=h,a===null?(h=i.child,i.child=null):(h=a.sibling,a.sibling=null),fu(i,!1,h,a,m);break;case"backwards":for(a=null,h=i.child,i.child=null;h!==null;){if(n=h.alternate,n!==null&&ka(n)===null){i.child=h;break}n=h.sibling,h.sibling=a,a=h,h=n}fu(i,!0,a,null,m);break;case"together":fu(i,!1,null,null,void 0);break;default:i.memoizedState=null}return i.child}function ja(n,i){(i.mode&1)===0&&n!==null&&(n.alternate=null,i.alternate=null,i.flags|=2)}function Fi(n,i,a){if(n!==null&&(i.dependencies=n.dependencies),Hr|=i.lanes,(a&i.childLanes)===0)return null;if(n!==null&&i.child!==n.child)throw Error(t(153));if(i.child!==null){for(n=i.child,a=vr(n,n.pendingProps),i.child=a,a.return=i;n.sibling!==null;)n=n.sibling,a=a.sibling=vr(n,n.pendingProps),a.return=i;a.sibling=null}return i.child}function Lv(n,i,a){switch(i.tag){case 3:Ep(i),Ms();break;case 5:Hh(i);break;case 1:Fn(i.type)&&Ca(i);break;case 4:Wc(i,i.stateNode.containerInfo);break;case 10:var c=i.type._context,h=i.memoizedProps.value;Ht(Ia,c._currentValue),c._currentValue=h;break;case 13:if(c=i.memoizedState,c!==null)return c.dehydrated!==null?(Ht(jt,jt.current&1),i.flags|=128,null):(a&i.child.childLanes)!==0?Tp(n,i,a):(Ht(jt,jt.current&1),n=Fi(n,i,a),n!==null?n.sibling:null);Ht(jt,jt.current&1);break;case 19:if(c=(a&i.childLanes)!==0,(n.flags&128)!==0){if(c)return Rp(n,i,a);i.flags|=128}if(h=i.memoizedState,h!==null&&(h.rendering=null,h.tail=null,h.lastEffect=null),Ht(jt,jt.current),c)break;return null;case 22:case 23:return i.lanes=0,yp(n,i,a)}return Fi(n,i,a)}var Cp,du,bp,Pp;Cp=function(n,i){for(var a=i.child;a!==null;){if(a.tag===5||a.tag===6)n.appendChild(a.stateNode);else if(a.tag!==4&&a.child!==null){a.child.return=a,a=a.child;continue}if(a===i)break;for(;a.sibling===null;){if(a.return===null||a.return===i)return;a=a.return}a.sibling.return=a.return,a=a.sibling}},du=function(){},bp=function(n,i,a,c){var h=n.memoizedProps;if(h!==c){n=i.stateNode,Br(xi.current);var m=null;switch(a){case"input":h=Me(n,h),c=Me(n,c),m=[];break;case"select":h=ie({},h,{value:void 0}),c=ie({},c,{value:void 0}),m=[];break;case"textarea":h=ft(n,h),c=ft(n,c),m=[];break;default:typeof h.onClick!="function"&&typeof c.onClick=="function"&&(n.onclick=Ta)}Ze(a,c);var E;a=null;for(de in h)if(!c.hasOwnProperty(de)&&h.hasOwnProperty(de)&&h[de]!=null)if(de==="style"){var k=h[de];for(E in k)k.hasOwnProperty(E)&&(a||(a={}),a[E]="")}else de!=="dangerouslySetInnerHTML"&&de!=="children"&&de!=="suppressContentEditableWarning"&&de!=="suppressHydrationWarning"&&de!=="autoFocus"&&(o.hasOwnProperty(de)?m||(m=[]):(m=m||[]).push(de,null));for(de in c){var G=c[de];if(k=h?.[de],c.hasOwnProperty(de)&&G!==k&&(G!=null||k!=null))if(de==="style")if(k){for(E in k)!k.hasOwnProperty(E)||G&&G.hasOwnProperty(E)||(a||(a={}),a[E]="");for(E in G)G.hasOwnProperty(E)&&k[E]!==G[E]&&(a||(a={}),a[E]=G[E])}else a||(m||(m=[]),m.push(de,a)),a=G;else de==="dangerouslySetInnerHTML"?(G=G?G.__html:void 0,k=k?k.__html:void 0,G!=null&&k!==G&&(m=m||[]).push(de,G)):de==="children"?typeof G!="string"&&typeof G!="number"||(m=m||[]).push(de,""+G):de!=="suppressContentEditableWarning"&&de!=="suppressHydrationWarning"&&(o.hasOwnProperty(de)?(G!=null&&de==="onScroll"&&Vt("scroll",n),m||k===G||(m=[])):(m=m||[]).push(de,G))}a&&(m=m||[]).push("style",a);var de=m;(i.updateQueue=de)&&(i.flags|=4)}},Pp=function(n,i,a,c){a!==c&&(i.flags|=4)};function Io(n,i){if(!Xt)switch(n.tailMode){case"hidden":i=n.tail;for(var a=null;i!==null;)i.alternate!==null&&(a=i),i=i.sibling;a===null?n.tail=null:a.sibling=null;break;case"collapsed":a=n.tail;for(var c=null;a!==null;)a.alternate!==null&&(c=a),a=a.sibling;c===null?i||n.tail===null?n.tail=null:n.tail.sibling=null:c.sibling=null}}function wn(n){var i=n.alternate!==null&&n.alternate.child===n.child,a=0,c=0;if(i)for(var h=n.child;h!==null;)a|=h.lanes|h.childLanes,c|=h.subtreeFlags&14680064,c|=h.flags&14680064,h.return=n,h=h.sibling;else for(h=n.child;h!==null;)a|=h.lanes|h.childLanes,c|=h.subtreeFlags,c|=h.flags,h.return=n,h=h.sibling;return n.subtreeFlags|=c,n.childLanes=a,i}function Dv(n,i,a){var c=i.pendingProps;switch(Ic(i),i.tag){case 2:case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return wn(i),null;case 1:return Fn(i.type)&&Ra(),wn(i),null;case 3:return c=i.stateNode,As(),Gt(Un),Gt(Mn),qc(),c.pendingContext&&(c.context=c.pendingContext,c.pendingContext=null),(n===null||n.child===null)&&(Da(i)?i.flags|=4:n===null||n.memoizedState.isDehydrated&&(i.flags&256)===0||(i.flags|=1024,ai!==null&&(Eu(ai),ai=null))),du(n,i),wn(i),null;case 5:Xc(i);var h=Br(bo.current);if(a=i.type,n!==null&&i.stateNode!=null)bp(n,i,a,c,h),n.ref!==i.ref&&(i.flags|=512,i.flags|=2097152);else{if(!c){if(i.stateNode===null)throw Error(t(166));return wn(i),null}if(n=Br(xi.current),Da(i)){c=i.stateNode,a=i.type;var m=i.memoizedProps;switch(c[_i]=i,c[wo]=m,n=(i.mode&1)!==0,a){case"dialog":Vt("cancel",c),Vt("close",c);break;case"iframe":case"object":case"embed":Vt("load",c);break;case"video":case"audio":for(h=0;h<So.length;h++)Vt(So[h],c);break;case"source":Vt("error",c);break;case"img":case"image":case"link":Vt("error",c),Vt("load",c);break;case"details":Vt("toggle",c);break;case"input":_e(c,m),Vt("invalid",c);break;case"select":c._wrapperState={wasMultiple:!!m.multiple},Vt("invalid",c);break;case"textarea":L(c,m),Vt("invalid",c)}Ze(a,m),h=null;for(var E in m)if(m.hasOwnProperty(E)){var k=m[E];E==="children"?typeof k=="string"?c.textContent!==k&&(m.suppressHydrationWarning!==!0&&wa(c.textContent,k,n),h=["children",k]):typeof k=="number"&&c.textContent!==""+k&&(m.suppressHydrationWarning!==!0&&wa(c.textContent,k,n),h=["children",""+k]):o.hasOwnProperty(E)&&k!=null&&E==="onScroll"&&Vt("scroll",c)}switch(a){case"input":tt(c),be(c,m,!0);break;case"textarea":tt(c),J(c);break;case"select":case"option":break;default:typeof m.onClick=="function"&&(c.onclick=Ta)}c=h,i.updateQueue=c,c!==null&&(i.flags|=4)}else{E=h.nodeType===9?h:h.ownerDocument,n==="http://www.w3.org/1999/xhtml"&&(n=ge(a)),n==="http://www.w3.org/1999/xhtml"?a==="script"?(n=E.createElement("div"),n.innerHTML="<script><\/script>",n=n.removeChild(n.firstChild)):typeof c.is=="string"?n=E.createElement(a,{is:c.is}):(n=E.createElement(a),a==="select"&&(E=n,c.multiple?E.multiple=!0:c.size&&(E.size=c.size))):n=E.createElementNS(n,a),n[_i]=i,n[wo]=c,Cp(n,i,!1,!1),i.stateNode=n;e:{switch(E=Ve(a,c),a){case"dialog":Vt("cancel",n),Vt("close",n),h=c;break;case"iframe":case"object":case"embed":Vt("load",n),h=c;break;case"video":case"audio":for(h=0;h<So.length;h++)Vt(So[h],n);h=c;break;case"source":Vt("error",n),h=c;break;case"img":case"image":case"link":Vt("error",n),Vt("load",n),h=c;break;case"details":Vt("toggle",n),h=c;break;case"input":_e(n,c),h=Me(n,c),Vt("invalid",n);break;case"option":h=c;break;case"select":n._wrapperState={wasMultiple:!!c.multiple},h=ie({},c,{value:void 0}),Vt("invalid",n);break;case"textarea":L(n,c),h=ft(n,c),Vt("invalid",n);break;default:h=c}Ze(a,h),k=h;for(m in k)if(k.hasOwnProperty(m)){var G=k[m];m==="style"?He(n,G):m==="dangerouslySetInnerHTML"?(G=G?G.__html:void 0,G!=null&&Je(n,G)):m==="children"?typeof G=="string"?(a!=="textarea"||G!=="")&&Le(n,G):typeof G=="number"&&Le(n,""+G):m!=="suppressContentEditableWarning"&&m!=="suppressHydrationWarning"&&m!=="autoFocus"&&(o.hasOwnProperty(m)?G!=null&&m==="onScroll"&&Vt("scroll",n):G!=null&&D(n,m,G,E))}switch(a){case"input":tt(n),be(n,c,!1);break;case"textarea":tt(n),J(n);break;case"option":c.value!=null&&n.setAttribute("value",""+Ee(c.value));break;case"select":n.multiple=!!c.multiple,m=c.value,m!=null?ct(n,!!c.multiple,m,!1):c.defaultValue!=null&&ct(n,!!c.multiple,c.defaultValue,!0);break;default:typeof h.onClick=="function"&&(n.onclick=Ta)}switch(a){case"button":case"input":case"select":case"textarea":c=!!c.autoFocus;break e;case"img":c=!0;break e;default:c=!1}}c&&(i.flags|=4)}i.ref!==null&&(i.flags|=512,i.flags|=2097152)}return wn(i),null;case 6:if(n&&i.stateNode!=null)Pp(n,i,n.memoizedProps,c);else{if(typeof c!="string"&&i.stateNode===null)throw Error(t(166));if(a=Br(bo.current),Br(xi.current),Da(i)){if(c=i.stateNode,a=i.memoizedProps,c[_i]=i,(m=c.nodeValue!==a)&&(n=jn,n!==null))switch(n.tag){case 3:wa(c.nodeValue,a,(n.mode&1)!==0);break;case 5:n.memoizedProps.suppressHydrationWarning!==!0&&wa(c.nodeValue,a,(n.mode&1)!==0)}m&&(i.flags|=4)}else c=(a.nodeType===9?a:a.ownerDocument).createTextNode(c),c[_i]=i,i.stateNode=c}return wn(i),null;case 13:if(Gt(jt),c=i.memoizedState,n===null||n.memoizedState!==null&&n.memoizedState.dehydrated!==null){if(Xt&&qn!==null&&(i.mode&1)!==0&&(i.flags&128)===0)Nh(),Ms(),i.flags|=98560,m=!1;else if(m=Da(i),c!==null&&c.dehydrated!==null){if(n===null){if(!m)throw Error(t(318));if(m=i.memoizedState,m=m!==null?m.dehydrated:null,!m)throw Error(t(317));m[_i]=i}else Ms(),(i.flags&128)===0&&(i.memoizedState=null),i.flags|=4;wn(i),m=!1}else ai!==null&&(Eu(ai),ai=null),m=!0;if(!m)return i.flags&65536?i:null}return(i.flags&128)!==0?(i.lanes=a,i):(c=c!==null,c!==(n!==null&&n.memoizedState!==null)&&c&&(i.child.flags|=8192,(i.mode&1)!==0&&(n===null||(jt.current&1)!==0?on===0&&(on=3):Au())),i.updateQueue!==null&&(i.flags|=4),wn(i),null);case 4:return As(),du(n,i),n===null&&Mo(i.stateNode.containerInfo),wn(i),null;case 10:return zc(i.type._context),wn(i),null;case 17:return Fn(i.type)&&Ra(),wn(i),null;case 19:if(Gt(jt),m=i.memoizedState,m===null)return wn(i),null;if(c=(i.flags&128)!==0,E=m.rendering,E===null)if(c)Io(m,!1);else{if(on!==0||n!==null&&(n.flags&128)!==0)for(n=i.child;n!==null;){if(E=ka(n),E!==null){for(i.flags|=128,Io(m,!1),c=E.updateQueue,c!==null&&(i.updateQueue=c,i.flags|=4),i.subtreeFlags=0,c=a,a=i.child;a!==null;)m=a,n=c,m.flags&=14680066,E=m.alternate,E===null?(m.childLanes=0,m.lanes=n,m.child=null,m.subtreeFlags=0,m.memoizedProps=null,m.memoizedState=null,m.updateQueue=null,m.dependencies=null,m.stateNode=null):(m.childLanes=E.childLanes,m.lanes=E.lanes,m.child=E.child,m.subtreeFlags=0,m.deletions=null,m.memoizedProps=E.memoizedProps,m.memoizedState=E.memoizedState,m.updateQueue=E.updateQueue,m.type=E.type,n=E.dependencies,m.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext}),a=a.sibling;return Ht(jt,jt.current&1|2),i.child}n=n.sibling}m.tail!==null&&Y()>Ps&&(i.flags|=128,c=!0,Io(m,!1),i.lanes=4194304)}else{if(!c)if(n=ka(E),n!==null){if(i.flags|=128,c=!0,a=n.updateQueue,a!==null&&(i.updateQueue=a,i.flags|=4),Io(m,!0),m.tail===null&&m.tailMode==="hidden"&&!E.alternate&&!Xt)return wn(i),null}else 2*Y()-m.renderingStartTime>Ps&&a!==1073741824&&(i.flags|=128,c=!0,Io(m,!1),i.lanes=4194304);m.isBackwards?(E.sibling=i.child,i.child=E):(a=m.last,a!==null?a.sibling=E:i.child=E,m.last=E)}return m.tail!==null?(i=m.tail,m.rendering=i,m.tail=i.sibling,m.renderingStartTime=Y(),i.sibling=null,a=jt.current,Ht(jt,c?a&1|2:a&1),i):(wn(i),null);case 22:case 23:return Tu(),c=i.memoizedState!==null,n!==null&&n.memoizedState!==null!==c&&(i.flags|=8192),c&&(i.mode&1)!==0?(Yn&1073741824)!==0&&(wn(i),i.subtreeFlags&6&&(i.flags|=8192)):wn(i),null;case 24:return null;case 25:return null}throw Error(t(156,i.tag))}function Nv(n,i){switch(Ic(i),i.tag){case 1:return Fn(i.type)&&Ra(),n=i.flags,n&65536?(i.flags=n&-65537|128,i):null;case 3:return As(),Gt(Un),Gt(Mn),qc(),n=i.flags,(n&65536)!==0&&(n&128)===0?(i.flags=n&-65537|128,i):null;case 5:return Xc(i),null;case 13:if(Gt(jt),n=i.memoizedState,n!==null&&n.dehydrated!==null){if(i.alternate===null)throw Error(t(340));Ms()}return n=i.flags,n&65536?(i.flags=n&-65537|128,i):null;case 19:return Gt(jt),null;case 4:return As(),null;case 10:return zc(i.type._context),null;case 22:case 23:return Tu(),null;case 24:return null;default:return null}}var qa=!1,Tn=!1,Iv=typeof WeakSet=="function"?WeakSet:Set,Qe=null;function Cs(n,i){var a=n.ref;if(a!==null)if(typeof a=="function")try{a(null)}catch(c){Kt(n,i,c)}else a.current=null}function hu(n,i,a){try{a()}catch(c){Kt(n,i,c)}}var Lp=!1;function Uv(n,i){if(Tc=ha,n=ch(),vc(n)){if("selectionStart"in n)var a={start:n.selectionStart,end:n.selectionEnd};else e:{a=(a=n.ownerDocument)&&a.defaultView||window;var c=a.getSelection&&a.getSelection();if(c&&c.rangeCount!==0){a=c.anchorNode;var h=c.anchorOffset,m=c.focusNode;c=c.focusOffset;try{a.nodeType,m.nodeType}catch{a=null;break e}var E=0,k=-1,G=-1,de=0,Pe=0,Fe=n,Ce=null;t:for(;;){for(var $e;Fe!==a||h!==0&&Fe.nodeType!==3||(k=E+h),Fe!==m||c!==0&&Fe.nodeType!==3||(G=E+c),Fe.nodeType===3&&(E+=Fe.nodeValue.length),($e=Fe.firstChild)!==null;)Ce=Fe,Fe=$e;for(;;){if(Fe===n)break t;if(Ce===a&&++de===h&&(k=E),Ce===m&&++Pe===c&&(G=E),($e=Fe.nextSibling)!==null)break;Fe=Ce,Ce=Fe.parentNode}Fe=$e}a=k===-1||G===-1?null:{start:k,end:G}}else a=null}a=a||{start:0,end:0}}else a=null;for(Ac={focusedElem:n,selectionRange:a},ha=!1,Qe=i;Qe!==null;)if(i=Qe,n=i.child,(i.subtreeFlags&1028)!==0&&n!==null)n.return=i,Qe=n;else for(;Qe!==null;){i=Qe;try{var rt=i.alternate;if((i.flags&1024)!==0)switch(i.tag){case 0:case 11:case 15:break;case 1:if(rt!==null){var st=rt.memoizedProps,en=rt.memoizedState,te=i.stateNode,q=te.getSnapshotBeforeUpdate(i.elementType===i.type?st:li(i.type,st),en);te.__reactInternalSnapshotBeforeUpdate=q}break;case 3:var se=i.stateNode.containerInfo;se.nodeType===1?se.textContent="":se.nodeType===9&&se.documentElement&&se.removeChild(se.documentElement);break;case 5:case 6:case 4:case 17:break;default:throw Error(t(163))}}catch(ze){Kt(i,i.return,ze)}if(n=i.sibling,n!==null){n.return=i.return,Qe=n;break}Qe=i.return}return rt=Lp,Lp=!1,rt}function Uo(n,i,a){var c=i.updateQueue;if(c=c!==null?c.lastEffect:null,c!==null){var h=c=c.next;do{if((h.tag&n)===n){var m=h.destroy;h.destroy=void 0,m!==void 0&&hu(i,a,m)}h=h.next}while(h!==c)}}function Ya(n,i){if(i=i.updateQueue,i=i!==null?i.lastEffect:null,i!==null){var a=i=i.next;do{if((a.tag&n)===n){var c=a.create;a.destroy=c()}a=a.next}while(a!==i)}}function pu(n){var i=n.ref;if(i!==null){var a=n.stateNode;switch(n.tag){case 5:n=a;break;default:n=a}typeof i=="function"?i(n):i.current=n}}function Dp(n){var i=n.alternate;i!==null&&(n.alternate=null,Dp(i)),n.child=null,n.deletions=null,n.sibling=null,n.tag===5&&(i=n.stateNode,i!==null&&(delete i[_i],delete i[wo],delete i[Pc],delete i[vv],delete i[_v])),n.stateNode=null,n.return=null,n.dependencies=null,n.memoizedProps=null,n.memoizedState=null,n.pendingProps=null,n.stateNode=null,n.updateQueue=null}function Np(n){return n.tag===5||n.tag===3||n.tag===4}function Ip(n){e:for(;;){for(;n.sibling===null;){if(n.return===null||Np(n.return))return null;n=n.return}for(n.sibling.return=n.return,n=n.sibling;n.tag!==5&&n.tag!==6&&n.tag!==18;){if(n.flags&2||n.child===null||n.tag===4)continue e;n.child.return=n,n=n.child}if(!(n.flags&2))return n.stateNode}}function mu(n,i,a){var c=n.tag;if(c===5||c===6)n=n.stateNode,i?a.nodeType===8?a.parentNode.insertBefore(n,i):a.insertBefore(n,i):(a.nodeType===8?(i=a.parentNode,i.insertBefore(n,a)):(i=a,i.appendChild(n)),a=a._reactRootContainer,a!=null||i.onclick!==null||(i.onclick=Ta));else if(c!==4&&(n=n.child,n!==null))for(mu(n,i,a),n=n.sibling;n!==null;)mu(n,i,a),n=n.sibling}function gu(n,i,a){var c=n.tag;if(c===5||c===6)n=n.stateNode,i?a.insertBefore(n,i):a.appendChild(n);else if(c!==4&&(n=n.child,n!==null))for(gu(n,i,a),n=n.sibling;n!==null;)gu(n,i,a),n=n.sibling}var gn=null,ci=!1;function dr(n,i,a){for(a=a.child;a!==null;)Up(n,i,a),a=a.sibling}function Up(n,i,a){if(yt&&typeof yt.onCommitFiberUnmount=="function")try{yt.onCommitFiberUnmount(lt,a)}catch{}switch(a.tag){case 5:Tn||Cs(a,i);case 6:var c=gn,h=ci;gn=null,dr(n,i,a),gn=c,ci=h,gn!==null&&(ci?(n=gn,a=a.stateNode,n.nodeType===8?n.parentNode.removeChild(a):n.removeChild(a)):gn.removeChild(a.stateNode));break;case 18:gn!==null&&(ci?(n=gn,a=a.stateNode,n.nodeType===8?bc(n.parentNode,a):n.nodeType===1&&bc(n,a),ho(n)):bc(gn,a.stateNode));break;case 4:c=gn,h=ci,gn=a.stateNode.containerInfo,ci=!0,dr(n,i,a),gn=c,ci=h;break;case 0:case 11:case 14:case 15:if(!Tn&&(c=a.updateQueue,c!==null&&(c=c.lastEffect,c!==null))){h=c=c.next;do{var m=h,E=m.destroy;m=m.tag,E!==void 0&&((m&2)!==0||(m&4)!==0)&&hu(a,i,E),h=h.next}while(h!==c)}dr(n,i,a);break;case 1:if(!Tn&&(Cs(a,i),c=a.stateNode,typeof c.componentWillUnmount=="function"))try{c.props=a.memoizedProps,c.state=a.memoizedState,c.componentWillUnmount()}catch(k){Kt(a,i,k)}dr(n,i,a);break;case 21:dr(n,i,a);break;case 22:a.mode&1?(Tn=(c=Tn)||a.memoizedState!==null,dr(n,i,a),Tn=c):dr(n,i,a);break;default:dr(n,i,a)}}function Fp(n){var i=n.updateQueue;if(i!==null){n.updateQueue=null;var a=n.stateNode;a===null&&(a=n.stateNode=new Iv),i.forEach(function(c){var h=Wv.bind(null,n,c);a.has(c)||(a.add(c),c.then(h,h))})}}function ui(n,i){var a=i.deletions;if(a!==null)for(var c=0;c<a.length;c++){var h=a[c];try{var m=n,E=i,k=E;e:for(;k!==null;){switch(k.tag){case 5:gn=k.stateNode,ci=!1;break e;case 3:gn=k.stateNode.containerInfo,ci=!0;break e;case 4:gn=k.stateNode.containerInfo,ci=!0;break e}k=k.return}if(gn===null)throw Error(t(160));Up(m,E,h),gn=null,ci=!1;var G=h.alternate;G!==null&&(G.return=null),h.return=null}catch(de){Kt(h,i,de)}}if(i.subtreeFlags&12854)for(i=i.child;i!==null;)Op(i,n),i=i.sibling}function Op(n,i){var a=n.alternate,c=n.flags;switch(n.tag){case 0:case 11:case 14:case 15:if(ui(i,n),Si(n),c&4){try{Uo(3,n,n.return),Ya(3,n)}catch(st){Kt(n,n.return,st)}try{Uo(5,n,n.return)}catch(st){Kt(n,n.return,st)}}break;case 1:ui(i,n),Si(n),c&512&&a!==null&&Cs(a,a.return);break;case 5:if(ui(i,n),Si(n),c&512&&a!==null&&Cs(a,a.return),n.flags&32){var h=n.stateNode;try{Le(h,"")}catch(st){Kt(n,n.return,st)}}if(c&4&&(h=n.stateNode,h!=null)){var m=n.memoizedProps,E=a!==null?a.memoizedProps:m,k=n.type,G=n.updateQueue;if(n.updateQueue=null,G!==null)try{k==="input"&&m.type==="radio"&&m.name!=null&&Se(h,m),Ve(k,E);var de=Ve(k,m);for(E=0;E<G.length;E+=2){var Pe=G[E],Fe=G[E+1];Pe==="style"?He(h,Fe):Pe==="dangerouslySetInnerHTML"?Je(h,Fe):Pe==="children"?Le(h,Fe):D(h,Pe,Fe,de)}switch(k){case"input":fe(h,m);break;case"textarea":w(h,m);break;case"select":var Ce=h._wrapperState.wasMultiple;h._wrapperState.wasMultiple=!!m.multiple;var $e=m.value;$e!=null?ct(h,!!m.multiple,$e,!1):Ce!==!!m.multiple&&(m.defaultValue!=null?ct(h,!!m.multiple,m.defaultValue,!0):ct(h,!!m.multiple,m.multiple?[]:"",!1))}h[wo]=m}catch(st){Kt(n,n.return,st)}}break;case 6:if(ui(i,n),Si(n),c&4){if(n.stateNode===null)throw Error(t(162));h=n.stateNode,m=n.memoizedProps;try{h.nodeValue=m}catch(st){Kt(n,n.return,st)}}break;case 3:if(ui(i,n),Si(n),c&4&&a!==null&&a.memoizedState.isDehydrated)try{ho(i.containerInfo)}catch(st){Kt(n,n.return,st)}break;case 4:ui(i,n),Si(n);break;case 13:ui(i,n),Si(n),h=n.child,h.flags&8192&&(m=h.memoizedState!==null,h.stateNode.isHidden=m,!m||h.alternate!==null&&h.alternate.memoizedState!==null||(xu=Y())),c&4&&Fp(n);break;case 22:if(Pe=a!==null&&a.memoizedState!==null,n.mode&1?(Tn=(de=Tn)||Pe,ui(i,n),Tn=de):ui(i,n),Si(n),c&8192){if(de=n.memoizedState!==null,(n.stateNode.isHidden=de)&&!Pe&&(n.mode&1)!==0)for(Qe=n,Pe=n.child;Pe!==null;){for(Fe=Qe=Pe;Qe!==null;){switch(Ce=Qe,$e=Ce.child,Ce.tag){case 0:case 11:case 14:case 15:Uo(4,Ce,Ce.return);break;case 1:Cs(Ce,Ce.return);var rt=Ce.stateNode;if(typeof rt.componentWillUnmount=="function"){c=Ce,a=Ce.return;try{i=c,rt.props=i.memoizedProps,rt.state=i.memoizedState,rt.componentWillUnmount()}catch(st){Kt(c,a,st)}}break;case 5:Cs(Ce,Ce.return);break;case 22:if(Ce.memoizedState!==null){zp(Fe);continue}}$e!==null?($e.return=Ce,Qe=$e):zp(Fe)}Pe=Pe.sibling}e:for(Pe=null,Fe=n;;){if(Fe.tag===5){if(Pe===null){Pe=Fe;try{h=Fe.stateNode,de?(m=h.style,typeof m.setProperty=="function"?m.setProperty("display","none","important"):m.display="none"):(k=Fe.stateNode,G=Fe.memoizedProps.style,E=G!=null&&G.hasOwnProperty("display")?G.display:null,k.style.display=Ie("display",E))}catch(st){Kt(n,n.return,st)}}}else if(Fe.tag===6){if(Pe===null)try{Fe.stateNode.nodeValue=de?"":Fe.memoizedProps}catch(st){Kt(n,n.return,st)}}else if((Fe.tag!==22&&Fe.tag!==23||Fe.memoizedState===null||Fe===n)&&Fe.child!==null){Fe.child.return=Fe,Fe=Fe.child;continue}if(Fe===n)break e;for(;Fe.sibling===null;){if(Fe.return===null||Fe.return===n)break e;Pe===Fe&&(Pe=null),Fe=Fe.return}Pe===Fe&&(Pe=null),Fe.sibling.return=Fe.return,Fe=Fe.sibling}}break;case 19:ui(i,n),Si(n),c&4&&Fp(n);break;case 21:break;default:ui(i,n),Si(n)}}function Si(n){var i=n.flags;if(i&2){try{e:{for(var a=n.return;a!==null;){if(Np(a)){var c=a;break e}a=a.return}throw Error(t(160))}switch(c.tag){case 5:var h=c.stateNode;c.flags&32&&(Le(h,""),c.flags&=-33);var m=Ip(n);gu(n,m,h);break;case 3:case 4:var E=c.stateNode.containerInfo,k=Ip(n);mu(n,k,E);break;default:throw Error(t(161))}}catch(G){Kt(n,n.return,G)}n.flags&=-3}i&4096&&(n.flags&=-4097)}function Fv(n,i,a){Qe=n,kp(n)}function kp(n,i,a){for(var c=(n.mode&1)!==0;Qe!==null;){var h=Qe,m=h.child;if(h.tag===22&&c){var E=h.memoizedState!==null||qa;if(!E){var k=h.alternate,G=k!==null&&k.memoizedState!==null||Tn;k=qa;var de=Tn;if(qa=E,(Tn=G)&&!de)for(Qe=h;Qe!==null;)E=Qe,G=E.child,E.tag===22&&E.memoizedState!==null?Hp(h):G!==null?(G.return=E,Qe=G):Hp(h);for(;m!==null;)Qe=m,kp(m),m=m.sibling;Qe=h,qa=k,Tn=de}Bp(n)}else(h.subtreeFlags&8772)!==0&&m!==null?(m.return=h,Qe=m):Bp(n)}}function Bp(n){for(;Qe!==null;){var i=Qe;if((i.flags&8772)!==0){var a=i.alternate;try{if((i.flags&8772)!==0)switch(i.tag){case 0:case 11:case 15:Tn||Ya(5,i);break;case 1:var c=i.stateNode;if(i.flags&4&&!Tn)if(a===null)c.componentDidMount();else{var h=i.elementType===i.type?a.memoizedProps:li(i.type,a.memoizedProps);c.componentDidUpdate(h,a.memoizedState,c.__reactInternalSnapshotBeforeUpdate)}var m=i.updateQueue;m!==null&&zh(i,m,c);break;case 3:var E=i.updateQueue;if(E!==null){if(a=null,i.child!==null)switch(i.child.tag){case 5:a=i.child.stateNode;break;case 1:a=i.child.stateNode}zh(i,E,a)}break;case 5:var k=i.stateNode;if(a===null&&i.flags&4){a=k;var G=i.memoizedProps;switch(i.type){case"button":case"input":case"select":case"textarea":G.autoFocus&&a.focus();break;case"img":G.src&&(a.src=G.src)}}break;case 6:break;case 4:break;case 12:break;case 13:if(i.memoizedState===null){var de=i.alternate;if(de!==null){var Pe=de.memoizedState;if(Pe!==null){var Fe=Pe.dehydrated;Fe!==null&&ho(Fe)}}}break;case 19:case 17:case 21:case 22:case 23:case 25:break;default:throw Error(t(163))}Tn||i.flags&512&&pu(i)}catch(Ce){Kt(i,i.return,Ce)}}if(i===n){Qe=null;break}if(a=i.sibling,a!==null){a.return=i.return,Qe=a;break}Qe=i.return}}function zp(n){for(;Qe!==null;){var i=Qe;if(i===n){Qe=null;break}var a=i.sibling;if(a!==null){a.return=i.return,Qe=a;break}Qe=i.return}}function Hp(n){for(;Qe!==null;){var i=Qe;try{switch(i.tag){case 0:case 11:case 15:var a=i.return;try{Ya(4,i)}catch(G){Kt(i,a,G)}break;case 1:var c=i.stateNode;if(typeof c.componentDidMount=="function"){var h=i.return;try{c.componentDidMount()}catch(G){Kt(i,h,G)}}var m=i.return;try{pu(i)}catch(G){Kt(i,m,G)}break;case 5:var E=i.return;try{pu(i)}catch(G){Kt(i,E,G)}}}catch(G){Kt(i,i.return,G)}if(i===n){Qe=null;break}var k=i.sibling;if(k!==null){k.return=i.return,Qe=k;break}Qe=i.return}}var Ov=Math.ceil,$a=R.ReactCurrentDispatcher,vu=R.ReactCurrentOwner,ti=R.ReactCurrentBatchConfig,Pt=0,hn=null,tn=null,vn=0,Yn=0,bs=ar(0),on=0,Fo=null,Hr=0,Ka=0,_u=0,Oo=null,kn=null,xu=0,Ps=1/0,Oi=null,Za=!1,yu=null,hr=null,Ja=!1,pr=null,Qa=0,ko=0,Su=null,el=-1,tl=0;function Ln(){return(Pt&6)!==0?Y():el!==-1?el:el=Y()}function mr(n){return(n.mode&1)===0?1:(Pt&2)!==0&&vn!==0?vn&-vn:yv.transition!==null?(tl===0&&(tl=bn()),tl):(n=Rt,n!==0||(n=window.event,n=n===void 0?16:Gd(n.type)),n)}function fi(n,i,a,c){if(50<ko)throw ko=0,Su=null,Error(t(185));Qt(n,a,c),((Pt&2)===0||n!==hn)&&(n===hn&&((Pt&2)===0&&(Ka|=a),on===4&&gr(n,vn)),Bn(n,c),a===1&&Pt===0&&(i.mode&1)===0&&(Ps=Y()+500,ba&&cr()))}function Bn(n,i){var a=n.callbackNode;Dr(n,i);var c=si(n,n===hn?vn:0);if(c===0)a!==null&&j(a),n.callbackNode=null,n.callbackPriority=0;else if(i=c&-c,n.callbackPriority!==i){if(a!=null&&j(a),i===1)n.tag===0?xv(Gp.bind(null,n)):Ch(Gp.bind(null,n)),mv(function(){(Pt&6)===0&&cr()}),a=null;else{switch(Ud(c)){case 1:a=We;break;case 4:a=it;break;case 16:a=Ye;break;case 536870912:a=_t;break;default:a=Ye}a=Zp(a,Vp.bind(null,n))}n.callbackPriority=i,n.callbackNode=a}}function Vp(n,i){if(el=-1,tl=0,(Pt&6)!==0)throw Error(t(327));var a=n.callbackNode;if(Ls()&&n.callbackNode!==a)return null;var c=si(n,n===hn?vn:0);if(c===0)return null;if((c&30)!==0||(c&n.expiredLanes)!==0||i)i=nl(n,c);else{i=c;var h=Pt;Pt|=2;var m=Xp();(hn!==n||vn!==i)&&(Oi=null,Ps=Y()+500,Gr(n,i));do try{zv();break}catch(k){Wp(n,k)}while(!0);Bc(),$a.current=m,Pt=h,tn!==null?i=0:(hn=null,vn=0,i=on)}if(i!==0){if(i===2&&(h=zt(n),h!==0&&(c=h,i=Mu(n,h))),i===1)throw a=Fo,Gr(n,0),gr(n,c),Bn(n,Y()),a;if(i===6)gr(n,c);else{if(h=n.current.alternate,(c&30)===0&&!kv(h)&&(i=nl(n,c),i===2&&(m=zt(n),m!==0&&(c=m,i=Mu(n,m))),i===1))throw a=Fo,Gr(n,0),gr(n,c),Bn(n,Y()),a;switch(n.finishedWork=h,n.finishedLanes=c,i){case 0:case 1:throw Error(t(345));case 2:Wr(n,kn,Oi);break;case 3:if(gr(n,c),(c&130023424)===c&&(i=xu+500-Y(),10<i)){if(si(n,0)!==0)break;if(h=n.suspendedLanes,(h&c)!==c){Ln(),n.pingedLanes|=n.suspendedLanes&h;break}n.timeoutHandle=Cc(Wr.bind(null,n,kn,Oi),i);break}Wr(n,kn,Oi);break;case 4:if(gr(n,c),(c&4194240)===c)break;for(i=n.eventTimes,h=-1;0<c;){var E=31-bt(c);m=1<<E,E=i[E],E>h&&(h=E),c&=~m}if(c=h,c=Y()-c,c=(120>c?120:480>c?480:1080>c?1080:1920>c?1920:3e3>c?3e3:4320>c?4320:1960*Ov(c/1960))-c,10<c){n.timeoutHandle=Cc(Wr.bind(null,n,kn,Oi),c);break}Wr(n,kn,Oi);break;case 5:Wr(n,kn,Oi);break;default:throw Error(t(329))}}}return Bn(n,Y()),n.callbackNode===a?Vp.bind(null,n):null}function Mu(n,i){var a=Oo;return n.current.memoizedState.isDehydrated&&(Gr(n,i).flags|=256),n=nl(n,i),n!==2&&(i=kn,kn=a,i!==null&&Eu(i)),n}function Eu(n){kn===null?kn=n:kn.push.apply(kn,n)}function kv(n){for(var i=n;;){if(i.flags&16384){var a=i.updateQueue;if(a!==null&&(a=a.stores,a!==null))for(var c=0;c<a.length;c++){var h=a[c],m=h.getSnapshot;h=h.value;try{if(!oi(m(),h))return!1}catch{return!1}}}if(a=i.child,i.subtreeFlags&16384&&a!==null)a.return=i,i=a;else{if(i===n)break;for(;i.sibling===null;){if(i.return===null||i.return===n)return!0;i=i.return}i.sibling.return=i.return,i=i.sibling}}return!0}function gr(n,i){for(i&=~_u,i&=~Ka,n.suspendedLanes|=i,n.pingedLanes&=~i,n=n.expirationTimes;0<i;){var a=31-bt(i),c=1<<a;n[a]=-1,i&=~c}}function Gp(n){if((Pt&6)!==0)throw Error(t(327));Ls();var i=si(n,0);if((i&1)===0)return Bn(n,Y()),null;var a=nl(n,i);if(n.tag!==0&&a===2){var c=zt(n);c!==0&&(i=c,a=Mu(n,c))}if(a===1)throw a=Fo,Gr(n,0),gr(n,i),Bn(n,Y()),a;if(a===6)throw Error(t(345));return n.finishedWork=n.current.alternate,n.finishedLanes=i,Wr(n,kn,Oi),Bn(n,Y()),null}function wu(n,i){var a=Pt;Pt|=1;try{return n(i)}finally{Pt=a,Pt===0&&(Ps=Y()+500,ba&&cr())}}function Vr(n){pr!==null&&pr.tag===0&&(Pt&6)===0&&Ls();var i=Pt;Pt|=1;var a=ti.transition,c=Rt;try{if(ti.transition=null,Rt=1,n)return n()}finally{Rt=c,ti.transition=a,Pt=i,(Pt&6)===0&&cr()}}function Tu(){Yn=bs.current,Gt(bs)}function Gr(n,i){n.finishedWork=null,n.finishedLanes=0;var a=n.timeoutHandle;if(a!==-1&&(n.timeoutHandle=-1,pv(a)),tn!==null)for(a=tn.return;a!==null;){var c=a;switch(Ic(c),c.tag){case 1:c=c.type.childContextTypes,c!=null&&Ra();break;case 3:As(),Gt(Un),Gt(Mn),qc();break;case 5:Xc(c);break;case 4:As();break;case 13:Gt(jt);break;case 19:Gt(jt);break;case 10:zc(c.type._context);break;case 22:case 23:Tu()}a=a.return}if(hn=n,tn=n=vr(n.current,null),vn=Yn=i,on=0,Fo=null,_u=Ka=Hr=0,kn=Oo=null,kr!==null){for(i=0;i<kr.length;i++)if(a=kr[i],c=a.interleaved,c!==null){a.interleaved=null;var h=c.next,m=a.pending;if(m!==null){var E=m.next;m.next=h,c.next=E}a.pending=c}kr=null}return n}function Wp(n,i){do{var a=tn;try{if(Bc(),Ba.current=Ga,za){for(var c=qt.memoizedState;c!==null;){var h=c.queue;h!==null&&(h.pending=null),c=c.next}za=!1}if(zr=0,dn=sn=qt=null,Po=!1,Lo=0,vu.current=null,a===null||a.return===null){on=1,Fo=i,tn=null;break}e:{var m=n,E=a.return,k=a,G=i;if(i=vn,k.flags|=32768,G!==null&&typeof G=="object"&&typeof G.then=="function"){var de=G,Pe=k,Fe=Pe.tag;if((Pe.mode&1)===0&&(Fe===0||Fe===11||Fe===15)){var Ce=Pe.alternate;Ce?(Pe.updateQueue=Ce.updateQueue,Pe.memoizedState=Ce.memoizedState,Pe.lanes=Ce.lanes):(Pe.updateQueue=null,Pe.memoizedState=null)}var $e=mp(E);if($e!==null){$e.flags&=-257,gp($e,E,k,m,i),$e.mode&1&&pp(m,de,i),i=$e,G=de;var rt=i.updateQueue;if(rt===null){var st=new Set;st.add(G),i.updateQueue=st}else rt.add(G);break e}else{if((i&1)===0){pp(m,de,i),Au();break e}G=Error(t(426))}}else if(Xt&&k.mode&1){var en=mp(E);if(en!==null){(en.flags&65536)===0&&(en.flags|=256),gp(en,E,k,m,i),Oc(Rs(G,k));break e}}m=G=Rs(G,k),on!==4&&(on=2),Oo===null?Oo=[m]:Oo.push(m),m=E;do{switch(m.tag){case 3:m.flags|=65536,i&=-i,m.lanes|=i;var te=dp(m,G,i);Bh(m,te);break e;case 1:k=G;var q=m.type,se=m.stateNode;if((m.flags&128)===0&&(typeof q.getDerivedStateFromError=="function"||se!==null&&typeof se.componentDidCatch=="function"&&(hr===null||!hr.has(se)))){m.flags|=65536,i&=-i,m.lanes|=i;var ze=hp(m,k,i);Bh(m,ze);break e}}m=m.return}while(m!==null)}qp(a)}catch(ot){i=ot,tn===a&&a!==null&&(tn=a=a.return);continue}break}while(!0)}function Xp(){var n=$a.current;return $a.current=Ga,n===null?Ga:n}function Au(){(on===0||on===3||on===2)&&(on=4),hn===null||(Hr&268435455)===0&&(Ka&268435455)===0||gr(hn,vn)}function nl(n,i){var a=Pt;Pt|=2;var c=Xp();(hn!==n||vn!==i)&&(Oi=null,Gr(n,i));do try{Bv();break}catch(h){Wp(n,h)}while(!0);if(Bc(),Pt=a,$a.current=c,tn!==null)throw Error(t(261));return hn=null,vn=0,on}function Bv(){for(;tn!==null;)jp(tn)}function zv(){for(;tn!==null&&!ae();)jp(tn)}function jp(n){var i=Kp(n.alternate,n,Yn);n.memoizedProps=n.pendingProps,i===null?qp(n):tn=i,vu.current=null}function qp(n){var i=n;do{var a=i.alternate;if(n=i.return,(i.flags&32768)===0){if(a=Dv(a,i,Yn),a!==null){tn=a;return}}else{if(a=Nv(a,i),a!==null){a.flags&=32767,tn=a;return}if(n!==null)n.flags|=32768,n.subtreeFlags=0,n.deletions=null;else{on=6,tn=null;return}}if(i=i.sibling,i!==null){tn=i;return}tn=i=n}while(i!==null);on===0&&(on=5)}function Wr(n,i,a){var c=Rt,h=ti.transition;try{ti.transition=null,Rt=1,Hv(n,i,a,c)}finally{ti.transition=h,Rt=c}return null}function Hv(n,i,a,c){do Ls();while(pr!==null);if((Pt&6)!==0)throw Error(t(327));a=n.finishedWork;var h=n.finishedLanes;if(a===null)return null;if(n.finishedWork=null,n.finishedLanes=0,a===n.current)throw Error(t(177));n.callbackNode=null,n.callbackPriority=0;var m=a.lanes|a.childLanes;if(Sn(n,m),n===hn&&(tn=hn=null,vn=0),(a.subtreeFlags&2064)===0&&(a.flags&2064)===0||Ja||(Ja=!0,Zp(Ye,function(){return Ls(),null})),m=(a.flags&15990)!==0,(a.subtreeFlags&15990)!==0||m){m=ti.transition,ti.transition=null;var E=Rt;Rt=1;var k=Pt;Pt|=4,vu.current=null,Uv(n,a),Op(a,n),av(Ac),ha=!!Tc,Ac=Tc=null,n.current=a,Fv(a),pe(),Pt=k,Rt=E,ti.transition=m}else n.current=a;if(Ja&&(Ja=!1,pr=n,Qa=h),m=n.pendingLanes,m===0&&(hr=null),Ut(a.stateNode),Bn(n,Y()),i!==null)for(c=n.onRecoverableError,a=0;a<i.length;a++)h=i[a],c(h.value,{componentStack:h.stack,digest:h.digest});if(Za)throw Za=!1,n=yu,yu=null,n;return(Qa&1)!==0&&n.tag!==0&&Ls(),m=n.pendingLanes,(m&1)!==0?n===Su?ko++:(ko=0,Su=n):ko=0,cr(),null}function Ls(){if(pr!==null){var n=Ud(Qa),i=ti.transition,a=Rt;try{if(ti.transition=null,Rt=16>n?16:n,pr===null)var c=!1;else{if(n=pr,pr=null,Qa=0,(Pt&6)!==0)throw Error(t(331));var h=Pt;for(Pt|=4,Qe=n.current;Qe!==null;){var m=Qe,E=m.child;if((Qe.flags&16)!==0){var k=m.deletions;if(k!==null){for(var G=0;G<k.length;G++){var de=k[G];for(Qe=de;Qe!==null;){var Pe=Qe;switch(Pe.tag){case 0:case 11:case 15:Uo(8,Pe,m)}var Fe=Pe.child;if(Fe!==null)Fe.return=Pe,Qe=Fe;else for(;Qe!==null;){Pe=Qe;var Ce=Pe.sibling,$e=Pe.return;if(Dp(Pe),Pe===de){Qe=null;break}if(Ce!==null){Ce.return=$e,Qe=Ce;break}Qe=$e}}}var rt=m.alternate;if(rt!==null){var st=rt.child;if(st!==null){rt.child=null;do{var en=st.sibling;st.sibling=null,st=en}while(st!==null)}}Qe=m}}if((m.subtreeFlags&2064)!==0&&E!==null)E.return=m,Qe=E;else e:for(;Qe!==null;){if(m=Qe,(m.flags&2048)!==0)switch(m.tag){case 0:case 11:case 15:Uo(9,m,m.return)}var te=m.sibling;if(te!==null){te.return=m.return,Qe=te;break e}Qe=m.return}}var q=n.current;for(Qe=q;Qe!==null;){E=Qe;var se=E.child;if((E.subtreeFlags&2064)!==0&&se!==null)se.return=E,Qe=se;else e:for(E=q;Qe!==null;){if(k=Qe,(k.flags&2048)!==0)try{switch(k.tag){case 0:case 11:case 15:Ya(9,k)}}catch(ot){Kt(k,k.return,ot)}if(k===E){Qe=null;break e}var ze=k.sibling;if(ze!==null){ze.return=k.return,Qe=ze;break e}Qe=k.return}}if(Pt=h,cr(),yt&&typeof yt.onPostCommitFiberRoot=="function")try{yt.onPostCommitFiberRoot(lt,n)}catch{}c=!0}return c}finally{Rt=a,ti.transition=i}}return!1}function Yp(n,i,a){i=Rs(a,i),i=dp(n,i,1),n=fr(n,i,1),i=Ln(),n!==null&&(Qt(n,1,i),Bn(n,i))}function Kt(n,i,a){if(n.tag===3)Yp(n,n,a);else for(;i!==null;){if(i.tag===3){Yp(i,n,a);break}else if(i.tag===1){var c=i.stateNode;if(typeof i.type.getDerivedStateFromError=="function"||typeof c.componentDidCatch=="function"&&(hr===null||!hr.has(c))){n=Rs(a,n),n=hp(i,n,1),i=fr(i,n,1),n=Ln(),i!==null&&(Qt(i,1,n),Bn(i,n));break}}i=i.return}}function Vv(n,i,a){var c=n.pingCache;c!==null&&c.delete(i),i=Ln(),n.pingedLanes|=n.suspendedLanes&a,hn===n&&(vn&a)===a&&(on===4||on===3&&(vn&130023424)===vn&&500>Y()-xu?Gr(n,0):_u|=a),Bn(n,i)}function $p(n,i){i===0&&((n.mode&1)===0?i=1:(i=At,At<<=1,(At&130023424)===0&&(At=4194304)));var a=Ln();n=Ii(n,i),n!==null&&(Qt(n,i,a),Bn(n,a))}function Gv(n){var i=n.memoizedState,a=0;i!==null&&(a=i.retryLane),$p(n,a)}function Wv(n,i){var a=0;switch(n.tag){case 13:var c=n.stateNode,h=n.memoizedState;h!==null&&(a=h.retryLane);break;case 19:c=n.stateNode;break;default:throw Error(t(314))}c!==null&&c.delete(i),$p(n,a)}var Kp;Kp=function(n,i,a){if(n!==null)if(n.memoizedProps!==i.pendingProps||Un.current)On=!0;else{if((n.lanes&a)===0&&(i.flags&128)===0)return On=!1,Lv(n,i,a);On=(n.flags&131072)!==0}else On=!1,Xt&&(i.flags&1048576)!==0&&bh(i,La,i.index);switch(i.lanes=0,i.tag){case 2:var c=i.type;ja(n,i),n=i.pendingProps;var h=xs(i,Mn.current);Ts(i,a),h=Kc(null,i,c,n,h,a);var m=Zc();return i.flags|=1,typeof h=="object"&&h!==null&&typeof h.render=="function"&&h.$$typeof===void 0?(i.tag=1,i.memoizedState=null,i.updateQueue=null,Fn(c)?(m=!0,Ca(i)):m=!1,i.memoizedState=h.state!==null&&h.state!==void 0?h.state:null,Gc(i),h.updater=Wa,i.stateNode=h,h._reactInternals=i,iu(i,c,n,a),i=au(null,i,c,!0,m,a)):(i.tag=0,Xt&&m&&Nc(i),Pn(null,i,h,a),i=i.child),i;case 16:c=i.elementType;e:{switch(ja(n,i),n=i.pendingProps,h=c._init,c=h(c._payload),i.type=c,h=i.tag=jv(c),n=li(c,n),h){case 0:i=ou(null,i,c,n,a);break e;case 1:i=Mp(null,i,c,n,a);break e;case 11:i=vp(null,i,c,n,a);break e;case 14:i=_p(null,i,c,li(c.type,n),a);break e}throw Error(t(306,c,""))}return i;case 0:return c=i.type,h=i.pendingProps,h=i.elementType===c?h:li(c,h),ou(n,i,c,h,a);case 1:return c=i.type,h=i.pendingProps,h=i.elementType===c?h:li(c,h),Mp(n,i,c,h,a);case 3:e:{if(Ep(i),n===null)throw Error(t(387));c=i.pendingProps,m=i.memoizedState,h=m.element,kh(n,i),Oa(i,c,null,a);var E=i.memoizedState;if(c=E.element,m.isDehydrated)if(m={element:c,isDehydrated:!1,cache:E.cache,pendingSuspenseBoundaries:E.pendingSuspenseBoundaries,transitions:E.transitions},i.updateQueue.baseState=m,i.memoizedState=m,i.flags&256){h=Rs(Error(t(423)),i),i=wp(n,i,c,a,h);break e}else if(c!==h){h=Rs(Error(t(424)),i),i=wp(n,i,c,a,h);break e}else for(qn=or(i.stateNode.containerInfo.firstChild),jn=i,Xt=!0,ai=null,a=Fh(i,null,c,a),i.child=a;a;)a.flags=a.flags&-3|4096,a=a.sibling;else{if(Ms(),c===h){i=Fi(n,i,a);break e}Pn(n,i,c,a)}i=i.child}return i;case 5:return Hh(i),n===null&&Fc(i),c=i.type,h=i.pendingProps,m=n!==null?n.memoizedProps:null,E=h.children,Rc(c,h)?E=null:m!==null&&Rc(c,m)&&(i.flags|=32),Sp(n,i),Pn(n,i,E,a),i.child;case 6:return n===null&&Fc(i),null;case 13:return Tp(n,i,a);case 4:return Wc(i,i.stateNode.containerInfo),c=i.pendingProps,n===null?i.child=Es(i,null,c,a):Pn(n,i,c,a),i.child;case 11:return c=i.type,h=i.pendingProps,h=i.elementType===c?h:li(c,h),vp(n,i,c,h,a);case 7:return Pn(n,i,i.pendingProps,a),i.child;case 8:return Pn(n,i,i.pendingProps.children,a),i.child;case 12:return Pn(n,i,i.pendingProps.children,a),i.child;case 10:e:{if(c=i.type._context,h=i.pendingProps,m=i.memoizedProps,E=h.value,Ht(Ia,c._currentValue),c._currentValue=E,m!==null)if(oi(m.value,E)){if(m.children===h.children&&!Un.current){i=Fi(n,i,a);break e}}else for(m=i.child,m!==null&&(m.return=i);m!==null;){var k=m.dependencies;if(k!==null){E=m.child;for(var G=k.firstContext;G!==null;){if(G.context===c){if(m.tag===1){G=Ui(-1,a&-a),G.tag=2;var de=m.updateQueue;if(de!==null){de=de.shared;var Pe=de.pending;Pe===null?G.next=G:(G.next=Pe.next,Pe.next=G),de.pending=G}}m.lanes|=a,G=m.alternate,G!==null&&(G.lanes|=a),Hc(m.return,a,i),k.lanes|=a;break}G=G.next}}else if(m.tag===10)E=m.type===i.type?null:m.child;else if(m.tag===18){if(E=m.return,E===null)throw Error(t(341));E.lanes|=a,k=E.alternate,k!==null&&(k.lanes|=a),Hc(E,a,i),E=m.sibling}else E=m.child;if(E!==null)E.return=m;else for(E=m;E!==null;){if(E===i){E=null;break}if(m=E.sibling,m!==null){m.return=E.return,E=m;break}E=E.return}m=E}Pn(n,i,h.children,a),i=i.child}return i;case 9:return h=i.type,c=i.pendingProps.children,Ts(i,a),h=Qn(h),c=c(h),i.flags|=1,Pn(n,i,c,a),i.child;case 14:return c=i.type,h=li(c,i.pendingProps),h=li(c.type,h),_p(n,i,c,h,a);case 15:return xp(n,i,i.type,i.pendingProps,a);case 17:return c=i.type,h=i.pendingProps,h=i.elementType===c?h:li(c,h),ja(n,i),i.tag=1,Fn(c)?(n=!0,Ca(i)):n=!1,Ts(i,a),up(i,c,h),iu(i,c,h,a),au(null,i,c,!0,n,a);case 19:return Rp(n,i,a);case 22:return yp(n,i,a)}throw Error(t(156,i.tag))};function Zp(n,i){return b(n,i)}function Xv(n,i,a,c){this.tag=n,this.key=a,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.ref=null,this.pendingProps=i,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=c,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function ni(n,i,a,c){return new Xv(n,i,a,c)}function Ru(n){return n=n.prototype,!(!n||!n.isReactComponent)}function jv(n){if(typeof n=="function")return Ru(n)?1:0;if(n!=null){if(n=n.$$typeof,n===$)return 11;if(n===ne)return 14}return 2}function vr(n,i){var a=n.alternate;return a===null?(a=ni(n.tag,i,n.key,n.mode),a.elementType=n.elementType,a.type=n.type,a.stateNode=n.stateNode,a.alternate=n,n.alternate=a):(a.pendingProps=i,a.type=n.type,a.flags=0,a.subtreeFlags=0,a.deletions=null),a.flags=n.flags&14680064,a.childLanes=n.childLanes,a.lanes=n.lanes,a.child=n.child,a.memoizedProps=n.memoizedProps,a.memoizedState=n.memoizedState,a.updateQueue=n.updateQueue,i=n.dependencies,a.dependencies=i===null?null:{lanes:i.lanes,firstContext:i.firstContext},a.sibling=n.sibling,a.index=n.index,a.ref=n.ref,a}function il(n,i,a,c,h,m){var E=2;if(c=n,typeof n=="function")Ru(n)&&(E=1);else if(typeof n=="string")E=5;else e:switch(n){case I:return Xr(a.children,h,m,i);case N:E=8,h|=8;break;case C:return n=ni(12,a,i,h|2),n.elementType=C,n.lanes=m,n;case ee:return n=ni(13,a,i,h),n.elementType=ee,n.lanes=m,n;case le:return n=ni(19,a,i,h),n.elementType=le,n.lanes=m,n;case re:return rl(a,h,m,i);default:if(typeof n=="object"&&n!==null)switch(n.$$typeof){case T:E=10;break e;case F:E=9;break e;case $:E=11;break e;case ne:E=14;break e;case ce:E=16,c=null;break e}throw Error(t(130,n==null?n:typeof n,""))}return i=ni(E,a,i,h),i.elementType=n,i.type=c,i.lanes=m,i}function Xr(n,i,a,c){return n=ni(7,n,c,i),n.lanes=a,n}function rl(n,i,a,c){return n=ni(22,n,c,i),n.elementType=re,n.lanes=a,n.stateNode={isHidden:!1},n}function Cu(n,i,a){return n=ni(6,n,null,i),n.lanes=a,n}function bu(n,i,a){return i=ni(4,n.children!==null?n.children:[],n.key,i),i.lanes=a,i.stateNode={containerInfo:n.containerInfo,pendingChildren:null,implementation:n.implementation},i}function qv(n,i,a,c,h){this.tag=i,this.containerInfo=n,this.finishedWork=this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.pendingContext=this.context=null,this.callbackPriority=0,this.eventTimes=yn(0),this.expirationTimes=yn(-1),this.entangledLanes=this.finishedLanes=this.mutableReadLanes=this.expiredLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=yn(0),this.identifierPrefix=c,this.onRecoverableError=h,this.mutableSourceEagerHydrationData=null}function Pu(n,i,a,c,h,m,E,k,G){return n=new qv(n,i,a,k,G),i===1?(i=1,m===!0&&(i|=8)):i=0,m=ni(3,null,null,i),n.current=m,m.stateNode=n,m.memoizedState={element:c,isDehydrated:a,cache:null,transitions:null,pendingSuspenseBoundaries:null},Gc(m),n}function Yv(n,i,a){var c=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:H,key:c==null?null:""+c,children:n,containerInfo:i,implementation:a}}function Jp(n){if(!n)return lr;n=n._reactInternals;e:{if(Wn(n)!==n||n.tag!==1)throw Error(t(170));var i=n;do{switch(i.tag){case 3:i=i.stateNode.context;break e;case 1:if(Fn(i.type)){i=i.stateNode.__reactInternalMemoizedMergedChildContext;break e}}i=i.return}while(i!==null);throw Error(t(171))}if(n.tag===1){var a=n.type;if(Fn(a))return Ah(n,a,i)}return i}function Qp(n,i,a,c,h,m,E,k,G){return n=Pu(a,c,!0,n,h,m,E,k,G),n.context=Jp(null),a=n.current,c=Ln(),h=mr(a),m=Ui(c,h),m.callback=i??null,fr(a,m,h),n.current.lanes=h,Qt(n,h,c),Bn(n,c),n}function sl(n,i,a,c){var h=i.current,m=Ln(),E=mr(h);return a=Jp(a),i.context===null?i.context=a:i.pendingContext=a,i=Ui(m,E),i.payload={element:n},c=c===void 0?null:c,c!==null&&(i.callback=c),n=fr(h,i,E),n!==null&&(fi(n,h,E,m),Fa(n,h,E)),E}function ol(n){if(n=n.current,!n.child)return null;switch(n.child.tag){case 5:return n.child.stateNode;default:return n.child.stateNode}}function em(n,i){if(n=n.memoizedState,n!==null&&n.dehydrated!==null){var a=n.retryLane;n.retryLane=a!==0&&a<i?a:i}}function Lu(n,i){em(n,i),(n=n.alternate)&&em(n,i)}function $v(){return null}var tm=typeof reportError=="function"?reportError:function(n){console.error(n)};function Du(n){this._internalRoot=n}al.prototype.render=Du.prototype.render=function(n){var i=this._internalRoot;if(i===null)throw Error(t(409));sl(n,i,null,null)},al.prototype.unmount=Du.prototype.unmount=function(){var n=this._internalRoot;if(n!==null){this._internalRoot=null;var i=n.containerInfo;Vr(function(){sl(null,n,null,null)}),i[Pi]=null}};function al(n){this._internalRoot=n}al.prototype.unstable_scheduleHydration=function(n){if(n){var i=kd();n={blockedOn:null,target:n,priority:i};for(var a=0;a<ir.length&&i!==0&&i<ir[a].priority;a++);ir.splice(a,0,n),a===0&&Hd(n)}};function Nu(n){return!(!n||n.nodeType!==1&&n.nodeType!==9&&n.nodeType!==11)}function ll(n){return!(!n||n.nodeType!==1&&n.nodeType!==9&&n.nodeType!==11&&(n.nodeType!==8||n.nodeValue!==" react-mount-point-unstable "))}function nm(){}function Kv(n,i,a,c,h){if(h){if(typeof c=="function"){var m=c;c=function(){var de=ol(E);m.call(de)}}var E=Qp(i,c,n,0,null,!1,!1,"",nm);return n._reactRootContainer=E,n[Pi]=E.current,Mo(n.nodeType===8?n.parentNode:n),Vr(),E}for(;h=n.lastChild;)n.removeChild(h);if(typeof c=="function"){var k=c;c=function(){var de=ol(G);k.call(de)}}var G=Pu(n,0,!1,null,null,!1,!1,"",nm);return n._reactRootContainer=G,n[Pi]=G.current,Mo(n.nodeType===8?n.parentNode:n),Vr(function(){sl(i,G,a,c)}),G}function cl(n,i,a,c,h){var m=a._reactRootContainer;if(m){var E=m;if(typeof h=="function"){var k=h;h=function(){var G=ol(E);k.call(G)}}sl(i,E,n,h)}else E=Kv(a,i,n,h,c);return ol(E)}Fd=function(n){switch(n.tag){case 3:var i=n.stateNode;if(i.current.memoizedState.isDehydrated){var a=rn(i.pendingLanes);a!==0&&(Nr(i,a|1),Bn(i,Y()),(Pt&6)===0&&(Ps=Y()+500,cr()))}break;case 13:Vr(function(){var c=Ii(n,1);if(c!==null){var h=Ln();fi(c,n,1,h)}}),Lu(n,1)}},rc=function(n){if(n.tag===13){var i=Ii(n,134217728);if(i!==null){var a=Ln();fi(i,n,134217728,a)}Lu(n,134217728)}},Od=function(n){if(n.tag===13){var i=mr(n),a=Ii(n,i);if(a!==null){var c=Ln();fi(a,n,i,c)}Lu(n,i)}},kd=function(){return Rt},Bd=function(n,i){var a=Rt;try{return Rt=n,i()}finally{Rt=a}},Ue=function(n,i,a){switch(i){case"input":if(fe(n,a),i=a.name,a.type==="radio"&&i!=null){for(a=n;a.parentNode;)a=a.parentNode;for(a=a.querySelectorAll("input[name="+JSON.stringify(""+i)+'][type="radio"]'),i=0;i<a.length;i++){var c=a[i];if(c!==n&&c.form===n.form){var h=Aa(c);if(!h)throw Error(t(90));at(c),fe(c,h)}}}break;case"textarea":w(n,a);break;case"select":i=a.value,i!=null&&ct(n,!!a.multiple,i,!1)}},xt=wu,Ne=Vr;var Zv={usingClientEntryPoint:!1,Events:[To,vs,Aa,Te,et,wu]},Bo={findFiberByHostInstance:Ir,bundleType:0,version:"18.3.1",rendererPackageName:"react-dom"},Jv={bundleType:Bo.bundleType,version:Bo.version,rendererPackageName:Bo.rendererPackageName,rendererConfig:Bo.rendererConfig,overrideHookState:null,overrideHookStateDeletePath:null,overrideHookStateRenamePath:null,overrideProps:null,overridePropsDeletePath:null,overridePropsRenamePath:null,setErrorHandler:null,setSuspenseHandler:null,scheduleUpdate:null,currentDispatcherRef:R.ReactCurrentDispatcher,findHostInstanceByFiber:function(n){return n=Pr(n),n===null?null:n.stateNode},findFiberByHostInstance:Bo.findFiberByHostInstance||$v,findHostInstancesForRefresh:null,scheduleRefresh:null,scheduleRoot:null,setRefreshHandler:null,getCurrentFiber:null,reconcilerVersion:"18.3.1-next-f1338f8080-20240426"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var ul=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!ul.isDisabled&&ul.supportsFiber)try{lt=ul.inject(Jv),yt=ul}catch{}}return zn.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=Zv,zn.createPortal=function(n,i){var a=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!Nu(i))throw Error(t(200));return Yv(n,i,null,a)},zn.createRoot=function(n,i){if(!Nu(n))throw Error(t(299));var a=!1,c="",h=tm;return i!=null&&(i.unstable_strictMode===!0&&(a=!0),i.identifierPrefix!==void 0&&(c=i.identifierPrefix),i.onRecoverableError!==void 0&&(h=i.onRecoverableError)),i=Pu(n,1,!1,null,null,a,!1,c,h),n[Pi]=i.current,Mo(n.nodeType===8?n.parentNode:n),new Du(i)},zn.findDOMNode=function(n){if(n==null)return null;if(n.nodeType===1)return n;var i=n._reactInternals;if(i===void 0)throw typeof n.render=="function"?Error(t(188)):(n=Object.keys(n).join(","),Error(t(268,n)));return n=Pr(i),n=n===null?null:n.stateNode,n},zn.flushSync=function(n){return Vr(n)},zn.hydrate=function(n,i,a){if(!ll(i))throw Error(t(200));return cl(null,n,i,!0,a)},zn.hydrateRoot=function(n,i,a){if(!Nu(n))throw Error(t(405));var c=a!=null&&a.hydratedSources||null,h=!1,m="",E=tm;if(a!=null&&(a.unstable_strictMode===!0&&(h=!0),a.identifierPrefix!==void 0&&(m=a.identifierPrefix),a.onRecoverableError!==void 0&&(E=a.onRecoverableError)),i=Qp(i,null,n,1,a??null,h,!1,m,E),n[Pi]=i.current,Mo(n),c)for(n=0;n<c.length;n++)a=c[n],h=a._getVersion,h=h(a._source),i.mutableSourceEagerHydrationData==null?i.mutableSourceEagerHydrationData=[a,h]:i.mutableSourceEagerHydrationData.push(a,h);return new al(i)},zn.render=function(n,i,a){if(!ll(i))throw Error(t(200));return cl(null,n,i,!1,a)},zn.unmountComponentAtNode=function(n){if(!ll(n))throw Error(t(40));return n._reactRootContainer?(Vr(function(){cl(null,null,n,!1,function(){n._reactRootContainer=null,n[Pi]=null})}),!0):!1},zn.unstable_batchedUpdates=wu,zn.unstable_renderSubtreeIntoContainer=function(n,i,a,c){if(!ll(a))throw Error(t(200));if(n==null||n._reactInternals===void 0)throw Error(t(38));return cl(n,i,a,!1,c)},zn.version="18.3.1-next-f1338f8080-20240426",zn}var um;function A0(){if(um)return Fu.exports;um=1;function s(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(s)}catch(e){console.error(e)}}return s(),Fu.exports=s_(),Fu.exports}var fm;function o_(){if(fm)return fl;fm=1;var s=A0();return fl.createRoot=s.createRoot,fl.hydrateRoot=s.hydrateRoot,fl}var R0=o_(),Yl=A0();const a_={cmd:"⌘",shift:"⇧",alt:"⌥",option:"⌥",ctrl:"⌃",enter:"↵",return:"↵",esc:"esc",tab:"⇥",up:"↑",down:"↓",left:"←",right:"→",backspace:"⌫"},l_=s=>s.split("+").map(e=>a_[e.trim().toLowerCase()]??e.trim().toUpperCase());function c_({rows:s,at:e}){return W.jsx(W.Fragment,{children:s.map(t=>t&&W.jsx("div",{className:"ss-keys","data-show":t.show,"data-at":e,"aria-hidden":!0,children:t.caps.map((r,o)=>W.jsx("kbd",{className:"ss-key","data-down":t.down,children:r},o))},t.id))})}const C0={x:0,y:0,width:0,height:0},b0=s=>typeof s=="string"?s:"at"in s?s.at:null,u_=(s,e)=>s?.offsetWidth&&s.getBoundingClientRect().width/s.offsetWidth||e||1;function vd(s,e){const t=s.getBoundingClientRect();return{left:t.left,top:t.top,scale:s.offsetWidth&&t.width/s.offsetWidth||e||1,borderX:s.clientLeft,borderY:s.clientTop}}function Zo(s,e,t,r=vd(s,t)){const o=e.getBoundingClientRect(),{scale:l}=r;return{x:(o.left-r.left)/l-r.borderX,y:(o.top-r.top)/l-r.borderY,width:o.width/l,height:o.height/l}}function f_(s,e,t,r=vd(s,t)){const o=Zo(s,e,t,r),l=getComputedStyle(e),u=l.transform,f=u&&u!=="none"?u.match(/^matrix\(([^)]+)\)$/):null;if(!f)return o;const[d,p,v,g,_,S]=f[1].split(",").map(Number);if(p||v||_||S||!d||!g)return o;const M=o.width/d,A=o.height/g,[y,x]=l.transformOrigin.split(" ").map(parseFloat);return{x:o.x-y*(1-d),y:o.y-x*(1-g),width:M,height:A}}const d_=s=>{const e=getComputedStyle(s);return e.transform!=="none"||e.translate&&e.translate!=="none"||e.scale&&e.scale!=="none"||e.rotate&&e.rotate!=="none"};function h_(s,e){let t=!0;for(let u=e;u&&u!==s;u=u.parentElement)if(d_(u)){t=!1;break}if(t)return Zo(s,e,1);let r=0,o=0,l=e;for(;l&&l!==s;){r+=l.offsetLeft,o+=l.offsetTop;const u=l.offsetParent;if(!u||!s.contains(u))break;l=u,l!==s&&(r+=l.clientLeft-l.scrollLeft,o+=l.clientTop-l.scrollTop)}return{x:r,y:o,width:e.offsetWidth,height:e.offsetHeight}}function dm(s,e){const t=Object.keys(s);return t.length!==Object.keys(e).length?!1:t.every(r=>{const o=s[r],l=e[r];return l&&Math.abs(o.x-l.x)<.5&&Math.abs(o.y-l.y)<.5&&Math.abs(o.width-l.width)<.5&&Math.abs(o.height-l.height)<.5})}function P0(s){const e=s.parentElement;if(!e?.classList.contains("ss-scroller"))return;const t=s.clientHeight,r=s.scrollHeight,o=r>t?Math.max(24,t/r*t):0,l=r>t?s.scrollTop/(r-t)*(t-o):0;e.style.setProperty("--ss-thumb-h",`${o}px`),e.style.setProperty("--ss-thumb-y",`${l}px`)}const p_={house:[.65,0,.1,1],through:[.8,0,.1,1],settle:[.05,.85,.3,1],enter:[.1,.8,.3,.95],trip:[.78,0,.17,1],camera:[.45,0,.1,1]};function m_(s){const[e,t,r,o]=p_[s],l=3*e,u=3*(r-e)-l,f=1-l-u,d=3*t,p=3*(o-t)-d,v=1-d-p,g=S=>((f*S+u)*S+l)*S,_=S=>(3*f*S+2*u)*S+l;return S=>{if(S<=0)return 0;if(S>=1)return 1;let M=S;for(let A=0;A<8;A++){const y=_(M);if(Math.abs(y)<1e-6)break;const x=M-(g(M)-S)/y;if(x<0||x>1)break;M=x}if(Math.abs(g(M)-S)>1e-6){let A=0,y=1;for(let x=0;x<40;x++)M=(A+y)/2,g(M)<S?A=M:y=M}return((v*M+p)*M+d)*M}}function L0(){try{return!1}catch{return!0}}function $s(s){L0()&&console.warn(`[stageshow] ${s}`)}const js=(s,e,t)=>Math.min(t,Math.max(e,s)),Vl=s=>s<.5?4*s*s*s:1-Math.pow(-2*s+2,3)/2,g_=s=>{const e=Math.sin(s*12.9898)*43758.5453;return e-Math.floor(e)},hm=s=>{s&&window.setTimeout(()=>s.removeAttribute("data-touching"),240)};class qs extends Error{}function v_(s,e){const{rootRef:t,cursorRef:r,pos:o,hovered:l,kindRef:u,keysRef:f,dragging:d,autoUsed:p,autoRef:v,scaleRef:g,speed:_,layout:S,cursor:M,resolve:A,place:y,remeasure:x,ripple:O,setState:D,setKind:R,setKeys:z,setLastKeys:H}=e,I=m_("enter"),N=()=>{if(s.aborted)throw new qs},C=(P,B)=>new Promise((Z,ue)=>{N();const he=()=>{B(K),s.removeEventListener("abort",he),ue(new qs)},K=P(()=>{s.removeEventListener("abort",he),s.aborted?ue(new qs):Z()});s.addEventListener("abort",he,{once:!0})}),T=()=>C(P=>requestAnimationFrame(P),cancelAnimationFrame),F=P=>C(B=>setTimeout(B,P/_),clearTimeout),$=P=>{let B=!0;const Z=()=>{B&&(B=!1,s.removeEventListener("abort",Z),P())};return s.addEventListener("abort",Z,{once:!0}),Z},ee=async(P,B)=>{const Z=performance.now(),ue=P/_;for(;;){N();const he=Math.min(1,(performance.now()-Z)/ue);if(B(he),he===1)return;await T()}},le=P=>{const B=[];for(let Z=P;Z&&Z!==t.current;Z=Z.parentElement)Z.hasAttribute("data-target")&&B.push(Z);return B},ne=P=>{const B=t.current;if(!B)return;const Z=B.querySelectorAll("[data-cursor]");if(!Z.length&&!p.current)return;Z.length&&(p.current=!0);const ue=B.getBoundingClientRect(),he=ue.width/B.offsetWidth||1,K=B.dataset.cursorBase??"pointer";let oe=K;B.setAttribute("data-hit","");const Ee=document.elementsFromPoint(ue.left+P.x*he,ue.top+P.y*he);B.removeAttribute("data-hit");const ye=Ee.find(we=>{if(!B.contains(we)||we.closest(".ss-cursor, .ss-keys, .ss-ripple")||getComputedStyle(we).pointerEvents==="none"&&!we.closest('[data-cursor], [data-target], button, a[href], [role="button"], [role="menuitem"], [role="option"], [role="tab"]'))return!1;let tt=1;for(let at=we;at&&at!==B.parentElement;at=at.parentElement){const U=getComputedStyle(at);if(U.visibility==="hidden")return!1;tt*=Number(U.opacity)}return tt>.15});if(ye){const we=ye.closest('[data-cursor], button, a[href], [role="button"], [role="menuitem"], [role="option"], [role="tab"]');oe=we&&B.contains(we)&&we.dataset.cursor?we.dataset.cursor:K,oe!==u.current&&R(oe);return}Z.forEach(we=>{const tt=we.getBoundingClientRect(),at=(tt.left-ue.left)/he,U=(tt.top-ue.top)/he;P.x>=at&&P.x<=at+tt.width/he&&P.y>=U&&P.y<=U+tt.height/he&&(oe=we.dataset.cursor)}),oe!==u.current&&R(oe)};v.current=ne,d.current||ne(o.current);const ce=P=>{if(l.current===P)return;const B=le(P);le(l.current).forEach(Z=>B.includes(Z)||Z.removeAttribute("data-hover")),B.forEach(Z=>Z.setAttribute("data-hover","")),l.current=P};let re=f.current.id,V=0;const me=P=>{const B=b0(P);return B===null?null:t.current?.querySelector(`[data-target="${B}"]`)??null},ie={get signal(){return s},put(P){s.aborted||D(B=>({...B,...typeof P=="function"?P(B):P}))},async set(P){N(),ie.put(P),await T(),await T(),v.current?.(o.current),N()},wait:async P=>{N(),await F(P)},rect:(P,B)=>{const Z=t.current,ue=Z?.querySelector(`[data-target="${P}"]`);return!Z||!ue?($s(`no element with data-target="${P}"`),C0):B?.layout?h_(Z,ue):Zo(Z,ue,g.current)},center:P=>A(P),caret(P,B){V++;const Z=me(P),ue=t.current;if(!Z||!ue)return 0;const he=ue.getBoundingClientRect(),K=he.width/ue.offsetWidth||1,oe=he.left+B.x*K,Ee=he.top+B.y*K,ye=[],we=document.createTreeWalker(Z,NodeFilter.SHOW_TEXT),tt=document.createRange();let at=0;const U=fe=>{for(let be=fe.parentElement;be;be=be===Z?null:be.parentElement){const xe=getComputedStyle(be);if(xe.opacity==="0"||xe.visibility==="hidden"||xe.display==="none")return!0}return!1};for(let fe=we.nextNode();fe;fe=we.nextNode()){const be=fe.textContent??"";if(!U(fe)){for(let xe=0;xe<be.length;xe++){tt.setStart(fe,xe),tt.setEnd(fe,xe+1);const Re=tt.getBoundingClientRect();(Re.width||Re.height)&&ye.push({left:Re.left,right:Re.right,mid:(Re.left+Re.right)/2,top:Re.top,bottom:Re.bottom,at:at+xe})}at+=be.length}}if(!ye.length||Ee<ye[0].top)return 0;if(Ee>ye[ye.length-1].bottom)return at;let Me=ye[0];for(const fe of ye)Math.abs((fe.top+fe.bottom)/2-Ee)<Math.abs((Me.top+Me.bottom)/2-Ee)&&(Me=fe);const _e=ye.filter(fe=>Math.abs(fe.top-Me.top)<(Me.bottom-Me.top)/2),Se=_e.find(fe=>fe.mid>oe);return Se?Se.at:_e[_e.length-1].at+1},async move(P,B){N();const Z={...o.current},ue=A(P),he=Math.hypot(ue.x-Z.x,ue.y-Z.y);if(he<.5)return ce(me(P));const K=le(me(P));ce(le(l.current).find(at=>K.includes(at))??null);const oe=B?.duration??js(260+he*.9,300,650),Ee=Vl,ye=Math.min(he*.08,24),we=-(ue.y-Z.y)/he,tt=(ue.x-Z.x)/he;await ee(oe,at=>{const U=Ee(at),Me=Math.sin(Math.PI*U)*ye,_e=B?.path?B.path(U,Z,ue):{x:Z.x+(ue.x-Z.x)*U+we*Me,y:Z.y+(ue.y-Z.y)*U+tt*Me};y(_e),ne(_e),B?.onMove&&Yl.flushSync(()=>B.onMove(_e,Z,at))}),N(),ce(me(P))},async click(P,B){N(),P!==void 0&&(await ie.move(P),await F(120)),N();const Z=P!==void 0?me(P):l.current,ue=r.current,he=M?.style==="touch",K=$(()=>{ue?.removeAttribute("data-pressed"),Z?.removeAttribute("data-pressed"),he&&hm(ue)});try{he&&(ue?.setAttribute("data-touching",""),await F(140),N());for(let oe=0;oe<(B?.double?2:1);oe++)oe&&await F(70),N(),ue?.setAttribute("data-pressed","true"),M?.ripple&&O(o.current),Z?.setAttribute("data-pressed",B?.right?"right":""),await F(B?.double?80:100),N(),ue?.removeAttribute("data-pressed"),Z?.removeAttribute("data-pressed")}finally{K()}},async scroll(P,B,Z){N();const ue=me(P);if(!ue)return;const he=ue.scrollTop;let K=typeof B=="number"?B:he;if(typeof B=="string"){const ye=me(B);ye&&(K=he+(ye.getBoundingClientRect().top-ue.getBoundingClientRect().top)/u_(t.current,g.current)-(Z?.offset??0))}if(K=js(K,0,ue.scrollHeight-ue.clientHeight),M){const ye=Zo(t.current,ue,g.current||1),we=o.current;we.x>=ye.x+8&&we.x<=ye.x+ye.width-8&&we.y>=ye.y+8&&we.y<=ye.y+ye.height-8||(await this.move({x:ye.x+ye.width*.6,y:ye.y+ye.height*.55}),await this.wait(120))}const oe=ue.parentElement?.classList.contains("ss-scroller")?ue.parentElement:null;oe?.setAttribute("data-scrolling","");const Ee=$(()=>oe?.removeAttribute("data-scrolling"));try{await ee(Z?.duration??js(420+Math.abs(K-he)*1.2,500,1400),ye=>{ue.scrollTop=he+(K-he)*Vl(ye),ue.toggleAttribute("data-scrolled",ue.scrollTop>.5),P0(ue)}),N()}finally{Ee()}x(),v.current?.(o.current)},async snap(P,B){N();const Z=B?t.current?.querySelector(`[data-target="${B}"]`):t.current;Z?.setAttribute("data-instant","");const ue=$(()=>Z?.removeAttribute("data-instant"));try{ie.put(P),await T(),await T(),N()}finally{ue()}},async key(P){N();const B=l_(P),Z=++re,ue=f.current;H(ue.caps.length?{...ue,show:!1,down:!1}:null),z({id:Z,caps:B,show:!1,down:!1}),await T(),await T(),N(),z({id:Z,caps:B,show:!0,down:!1}),await F(180),N(),z({id:Z,caps:B,show:!0,down:!0}),await F(140),N(),z({id:Z,caps:B,show:!0,down:!1}),F(600).then(()=>{re===Z&&!s.aborted&&z({id:Z,caps:B,show:!1,down:!1})},he=>{he instanceof qs||console.error("[stageshow] script error",he)})},async stagger(P,B,Z=60){await Promise.all(P.map(async(ue,he)=>{he&&await F(Z*he),N(),await B(ue,he)}))},mark(P){s.aborted||t.current?.setAttribute("data-mark",P)},async cursor(P){N(),R(P),await T()},async type(P,B,Z){const ue=Z?.interval??35;for(let he=0;he<=B.length;he++)N(),D(K=>({...K,[P]:B.slice(0,he)})),await F(ue*(.7+.6*g_(he)))},place(P){if(s.aborted)return;const B=A(P);y(B),v.current?.(B)},async enter(P,B){N();const Z=A(P),ue=t.current,he={x:0,y:0,w:ue.offsetWidth,h:ue.offsetHeight},K=40,oe=[Z.x-he.x,he.x+he.w-Z.x,Z.y-he.y,he.y+he.h-Z.y],Ee=oe.indexOf(Math.min(...oe)),ye=Ee===0?{x:he.x-K,y:Z.y+he.h*.12}:Ee===1?{x:he.x+he.w+K*.4,y:Z.y+he.h*.12}:Ee===2?{x:Z.x-he.w*.06,y:he.y-K}:{x:Z.x+he.w*.06,y:he.y+he.h+K*.4};y(ye),ce(null),await ee(B?.duration??700,we=>{const tt=I(we),at={x:ye.x+(Z.x-ye.x)*tt,y:ye.y+(Z.y-ye.y)*tt};y(at),ne(at)}),N(),ce(me(P))},async drag(P,B,Z){N();const ue={...o.current},he=A(P),K=Math.hypot(he.x-ue.x,he.y-ue.y);ce(null);const oe=u.current,Ee=oe==="ibeam"||oe==="crosshair",ye=!Ee&&Z?.cursor!=="preserve",we=M?.style==="touch",tt=fe=>{const xe=1.1428571428571428;return fe<.25?fe*fe/(2*.25)*xe:(fe-.25/2)*xe};we&&(r.current?.setAttribute("data-touching",""),await F(140),N());const at=we?r.current?.querySelector(".ss-cursor__streak")??null:null,U=[],Me=fe=>{U.unshift({...fe}),U.length>9&&U.pop();const be=U[U.length-1],xe=fe.x-be.x,Re=fe.y-be.y,ct=Math.min(Math.hypot(xe,Re),100);at&&(at.style.width=`${ct}px`,at.style.left=`${-ct}px`,at.style.transform=`rotate(${Math.atan2(Re,xe)}rad)`)};d.current=!0;const _e=r.current,Se=$(()=>{d.current=!1,_e?.removeAttribute("data-pressed"),_e?.removeAttribute("data-swiping"),we&&hm(_e)});try{_e?.setAttribute("data-pressed","true"),await F(we?170:60),we&&(at&&(at.style.width="0px"),_e?.setAttribute("data-swiping","")),N(),ye&&!we&&R("grab"),we||await F(70),N(),_e?.removeAttribute("data-pressed");const fe=Ee?0:Math.min(K*.06,18),be=K?-(he.y-ue.y)/K:0,xe=K?(he.x-ue.x)/K:0,Re=Ee&&Math.abs(he.y-ue.y)>6;Re&&he.y>ue.y&&he.x<ue.x-2&&$s("a text selection that ends left of where it starts overshoots and shrinks back; select text that starts a line, or fits on one");const ct=V;await ee(we?Z?.duration??js(180+K*.5,240,300):Z?.duration??js(360+K*1.1,450,900),ft=>{const L=we?tt(ft):Vl(ft),w=Math.sin(Math.PI*L)*fe,J=Re?1-(1-L)*(1-L):L,ge=Re?L*L:L,Ae=Z?.path?.(L,ue,he)??{x:ue.x+(he.x-ue.x)*ge+be*w,y:ue.y+(he.y-ue.y)*J+xe*w};Yl.flushSync(()=>B?.(Ae,ue,ft)),y(Ae),we&&Me(Ae)}),Ee&&B&&V===ct&&$s("selection drift: a text selection drag never read a.caret(), so the highlight is not under the I-beam; set it from a.caret(name, at) in onMove"),N(),ye&&!we&&R(oe==="grab"?"pointer":oe)}finally{Se()}v.current?.(he)},layout:S};for(const P of Object.keys(ie)){const B=ie[P];typeof B=="function"&&(ie[P]=(...Z)=>{const ue=B.apply(ie,Z);return ue instanceof Promise&&ue.catch(he=>{he instanceof qs||console.error("[stageshow] script error",he)}),ue})}return ie}function __(s,e,t,r){const o=Object.keys(e).filter(l=>JSON.stringify(s[l])!==JSON.stringify(e[l]));o.length&&$s(`loop seam: state still differs from initial at the end of the script (${o.join(", ")})`),r&&Math.hypot(t.x-r.x,t.y-r.y)>1&&$s("loop seam: cursor does not end where it starts")}function x_(){return W.jsx("svg",{height:"24",width:"24",viewBox:"0 0 32 32",fill:"none",children:W.jsxs("g",{transform:"translate(10 7)",children:[W.jsx("path",{d:"m6.148 18.473 1.863-1.003 1.615-.839-2.568-4.816h4.332l-11.379-11.408v16.015l3.316-3.221z",fill:"#fff"}),W.jsx("path",{d:"m6.431 17 1.765-.941-2.775-5.202h3.604l-8.025-8.043v11.188l2.53-2.442z",fill:"#000"})]})})}function y_(){return W.jsxs("svg",{width:"10",height:"16",viewBox:"0 0 10 16",fill:"none",overflow:"visible",children:[W.jsx("path",{d:"M3 1H7M3 15H7M5 1V15",style:{stroke:"var(--ss-cursor-edge, #fff)"},strokeWidth:"2.6",strokeLinecap:"round"}),W.jsx("path",{d:"M3 1H7M3 15H7M5 1V15",style:{stroke:"var(--ss-cursor-line, #000)"},strokeWidth:"1",strokeLinecap:"round"})]})}function S_(){return W.jsxs("svg",{width:"17",height:"17",viewBox:"0 0 17 17",fill:"none",overflow:"visible",children:[W.jsx("path",{d:"M8.5 0V17M0 8.5H17",style:{stroke:"var(--ss-cursor-edge, #fff)"},strokeWidth:"2.6"}),W.jsx("path",{d:"M8.5 0V17M0 8.5H17",style:{stroke:"var(--ss-cursor-line, #000)"},strokeWidth:"1"})]})}function M_(){return W.jsxs("svg",{width:"26",height:"26",viewBox:"0 0 32 32",fill:"none",children:[W.jsx("path",{d:"M10.6 6a1.7 1.7 0 0 1 3.4 0v6.6a1.3 1.3 0 0 1 2.6 0v.7a1.3 1.3 0 0 1 2.6 0v.7a1.3 1.3 0 0 1 2.6 0V19c0 3.1-2 5.6-5 5.6h-2.6c-2 0-3.3-.9-4.4-2.4l-3.1-4.1c-.6-.9-.4-2 .5-2.5.8-.4 1.7-.2 2.3.5l1.1 1.4V6Z",fill:"#fff",stroke:"#000",strokeWidth:"1.1",strokeLinejoin:"round"}),W.jsx("path",{d:"M14 12.6v3.6M16.6 13.3v3M19.2 14v2.6",stroke:"#000",strokeWidth:"1",strokeLinecap:"round"})]})}function E_(){return W.jsx("svg",{width:"26",height:"26",viewBox:"0 0 32 32",fill:"none",children:W.jsxs("g",{transform:"translate(7 6)",children:[W.jsx("path",{d:"m4.5557 8.5742c-.098-.375-.196-.847-.406-1.552-.167-.557-.342-.859-.47-1.233-.155-.455-.303-.721-.496-1.181-.139-.329-.364-1.048-.457-1.44-.119-.509.033-.924.244-1.206.253-.339.962-.49 1.357-.351.371.13.744.512.916.788.288.46.357.632.717 1.542.393.992.564 1.918.611 2.231l.085.452c-.001-.04-.043-1.122-.044-1.162-.035-1.029-.06-1.823-.038-2.939.002-.126.064-.587.084-.715.078-.5.305-.8.673-.979.412-.201.926-.215 1.401-.017.423.173.626.55.687 1.022.014.109.094.987.093 1.107-.013 1.025.006 1.641.015 2.174.004.231.003 1.625.017 1.469.061-.656.094-3.189.344-3.942.144-.433.405-.746.794-.929.431-.203 1.113-.07 1.404.243.285.305.446.692.482 1.153.032.405-.019.897-.02 1.245 0 .867-.021 1.324-.037 2.121-.001.038-.015.298.023.182.094-.28.188-.542.266-.745.049-.125.241-.614.359-.859.114-.234.211-.369.415-.688.2-.313.415-.448.668-.561.54-.235 1.109.112 1.301.591.086.215.009.713-.028 1.105-.061.647-.254 1.306-.352 1.648-.128.447-.274 1.235-.34 1.601-.072.394-.234 1.382-.359 1.82-.086.301-.371.978-.652 1.384 0 0-1.074 1.25-1.192 1.812-.117.563-.078.567-.101.965-.024.399.121.923.121.923s-.802.104-1.234.034c-.391-.062-.875-.841-1-1.078-.172-.328-.539-.265-.682-.023-.225.383-.709 1.07-1.051 1.113-.668.084-2.054.03-3.139.02 0 0 .185-1.011-.227-1.358-.305-.26-.83-.784-1.144-1.06l-.832-.921c-.284-.36-.629-1.093-1.243-1.985-.348-.504-1.027-1.085-1.284-1.579-.223-.425-.331-.954-.19-1.325.225-.594.675-.897 1.362-.832.519.05.848.206 1.238.537.225.19.573.534.75.748.163.195.203.276.377.509.23.307.302.459.214.121",fill:"#fff"}),W.jsxs("g",{stroke:"#000",strokeLinecap:"round",strokeWidth:".75",children:[W.jsx("path",{d:"m4.5557 8.5742c-.098-.375-.196-.847-.406-1.552-.167-.557-.342-.859-.47-1.233-.155-.455-.303-.721-.496-1.181-.139-.329-.364-1.048-.457-1.44-.119-.509.033-.924.244-1.206.253-.339.962-.49 1.357-.351.371.13.744.512.916.788.288.46.357.632.717 1.542.393.992.564 1.918.611 2.231l.085.452c-.001-.04-.043-1.122-.044-1.162-.035-1.029-.06-1.823-.038-2.939.002-.126.064-.587.084-.715.078-.5.305-.8.673-.979.412-.201.926-.215 1.401-.017.423.173.626.55.687 1.022.014.109.094.987.093 1.107-.013 1.025.006 1.641.015 2.174.004.231.003 1.625.017 1.469.061-.656.094-3.189.344-3.942.144-.433.405-.746.794-.929.431-.203 1.113-.07 1.404.243.285.305.446.692.482 1.153.032.405-.019.897-.02 1.245 0 .867-.021 1.324-.037 2.121-.001.038-.015.298.023.182.094-.28.188-.542.266-.745.049-.125.241-.614.359-.859.114-.234.211-.369.415-.688.2-.313.415-.448.668-.561.54-.235 1.109.112 1.301.591.086.215.009.713-.028 1.105-.061.647-.254 1.306-.352 1.648-.128.447-.274 1.235-.34 1.601-.072.394-.234 1.382-.359 1.82-.086.301-.371.978-.652 1.384 0 0-1.074 1.25-1.192 1.812-.117.563-.078.567-.101.965-.024.399.121.923.121.923s-.802.104-1.234.034c-.391-.062-.875-.841-1-1.078-.172-.328-.539-.265-.682-.023-.225.383-.709 1.07-1.051 1.113-.668.084-2.054.03-3.139.02 0 0 .185-1.011-.227-1.358-.305-.26-.83-.784-1.144-1.06l-.832-.921c-.284-.36-.629-1.093-1.243-1.985-.348-.504-1.027-1.085-1.284-1.579-.223-.425-.331-.954-.19-1.325.225-.594.675-.897 1.362-.832.519.05.848.206 1.238.537.225.19.573.534.75.748.163.195.203.276.377.509.23.307.302.459.214.121",strokeLinejoin:"round"}),W.jsx("path",{d:"m11.566 12.734v-3.459"}),W.jsx("path",{d:"m9.551 12.746-.016-3.473"}),W.jsx("path",{d:"m7.555 9.305.021 3.426"})]})]})})}function w_(){return W.jsx("svg",{width:"30",height:"30",viewBox:"0 0 32 32",fill:"none",children:W.jsxs("g",{transform:"translate(8 9)",children:[W.jsx("path",{d:"m3.44281398 1.68449726c-.74326136.27630142-1.05584685.8131257-1.07636853 1.38003696-.01344897.37336893.06665513.72649286.23114214 1.18694303-.02596219-.07267623.09676488.29282004.12116236.37362273.05052942.16918921-.4865367-.05865774-.81377307.00741883-.36363321.07113868-.84783757.38332307-1.10006887.79754775-.29643467.48542737-.3109609 1.04368567-.08235979 2.04824266.12491868.54736183.36572145 1.00836814.71076689 1.44594879.15329951.1944118.5713628.64726015.60307236.6875974l.84854343.94062339c.15080214.1358526.25794954.2361946.57590427.5380259.3147558.2987762.4647038.4380078.60308951.555976.05846214.0492474.10784267.1797116.12740685.3736249.01609788.1595565.01049553.3375341-.0090192.5090254-.00674888.0593077-.01325791.1020883-.01698742.1224696-.04189161.228932.13269563.4403386.36541902.4424835.21585671.0019894.38528595.0046546.82216479.0123538.09483476.0016698.09483476.0016698.18993053.0033129 1.16876447.0200186 1.75308289.0147904 2.17807912-.0385723.45429894-.0572869.92650915-.6110188 1.32698393-1.2957591.34289141.6108338.81859723 1.2057867 1.2995685 1.2820532.1510118.0244148.3353555.0322555.548787.0275887.1606725-.0035131.3307029-.0140241.5021961-.0293376.1276907-.0114022.2293359-.0228648.29003-.0307451.2258836-.0293282.373669-.251611.3133108-.4712481-.0130351-.0474332-.0339838-.1345011-.0551094-.2441635-.0245945-.1276687-.0423383-.2523857-.0503381-.365988-.0050217-.0713101-.0059948-.1359317-.0027687-.1918983.0059157-.0980798.0077938-.1530073.0108033-.281125.0010795-.0448938.0010795-.0448938.0024606-.0845172.0054208-.1364475.0233824-.2649146.0815132-.544638.0250088-.1201275.1473169-.352189.3398902-.639435.0571394-.0852302.1195783-.1742239.1864664-.26609712.1272143-.17473362.2641361-.35131772.4011075-.52030772.082051-.10123129.145482-.17695689.1808122-.21807676.2967593-.42378347.612817-1.11823437.7291396-1.52536348.1117407-.39153936.202351-1.12501196.254373-1.81690429.029923-.39968605.0410555-.72381216.0410555-1.23011613.0000742-.09758414.0000742-.09758414.0002975-.17670236.0003569-.11115478.0003569-.11115478.000115-.20711835-.0008934-.15683883-.0055282-.31323355-.0207085-.69507578-.0313109-.81293139-.4771727-1.33911388-1.1344906-1.44058831-.559108-.08631314-1.0586051.08188477-1.2779293.31625977-.0755526.08073733.0036753-.2781823-.2159489-.62316278-.1644465-.25841586-.593184-.58905957-.9209287-.65355552-.335487-.06535532-.73539548-.05811715-1.1017193.00667481-.32093157.05742909-.68608434.33741751-.87176225.64688068-.12411885.20686477.03884667-.00592296-.09368743-.23401341-.18231052-.31422641-.60754287-.59486422-1.01411454-.67799709-.34643562-.07139428-.74182572-.04452925-1.09945614.0633873-.43336319.1291117-1.01795827.61460976-.94899189 1.15552627-.34375-.54091651-1.25026717-.691379-1.97906097-.42111797z",fill:"#000"}),W.jsx("path",{d:"m7.31951013 1.62138197c.20710357.04234751.44724204.20083012.51632974.31990811.08404358.1446387.15562749.36413806.21048667.6366124.02933373.14569467.12179446 1.2125285.29383112 1.32370243.41279229.04533731.41279229.04533731.52658055-.12364345.03545705-.07383858.03545705-.07383858.04226523-.1029106.01416796-.06009544.02463332-.12677987.0351322-.21754028l.00854738-.07915386.00047673-.00942804.00327525-.03167185c.01085148-.11424313.04184125-.4312127.05388392-.53034902.03788792-.31189663.08766449-.52757784.13944093-.6138719.0713024-.11883734.31942298-.28274442.43149612-.30279961.2804398-.04960082.58940103-.05519288.82623993-.00905543.1084394.02134018.3709471.22378689.432331.32024744.1291079.20279957.2524316.84889766.3225486 1.4970065-.0102194.04624251-.0102194.04624251.1640069.28984194.5843296-.06677889.5843296-.06677889.5703629-.17490247.0159511-.03856429.0284824-.08294031.045969-.15118961.0423876-.16089067.0697594-.25204451.111066-.35549917.0288558-.07227096.0592914-.13391873.0904889-.18278042.1209187-.19031132.4335712-.319392.7077174-.27707028.2943447.04543991.4816904.26653537.4994912.72869815.0148821.37434892.0193146.5239164.0201469.6700184l-.0004247.37954865c0 .48831141-.0104951.79388164-.0389535 1.17400348-.0480918.63962116-.1348512 1.34192123-.227649 1.66708484-.0946325.33121345-.3766371.95084197-.6003915 1.27298482-.0161892.01580846-.0841508.09694273-.1710333.20413492-.1445842.17838247-.2892181.36491271-.4247891.5511244-.0723398.09936149-.1402862.19620479-.2030964.2898938-.2440054.36396314-.400553.66098894-.4512157.90434304-.0659304.3172546-.0893838.4850003-.0966379.6675968-.0017072.0490782-.0017072.0490782-.002845.096677-.0028064.119476-.004437.1671639-.0097087.2545848-.0052654.091322-.0038193.187354.00332.2887353.0103318.1467182.1058713.3478531.1058713.3478531s-.2321503-.0119819-.3742084-.0088758c-.1718098.0037567-.3147843-.0023244-.4138162-.0183342-.1440353-.0228411-.53014068-.5057331-.7278511-.8821737-.30227042-.5764228-1.03604858-.5484427-1.33684295-.0394061-.26854779.4591613-.65918083.9172326-.7740684.9317199-.37404082.0469647-.94643778.0520862-2.07160079.0328144-.09480875-.0016381-.46003446-.0128683-.64600494-.0157445-.18597048-.0028763.05008807-.1790283.02786486-.399297-.03726222-.36933-.15125405-.6704984-.38877094-.8705429-.12241569-.1043631-.26774964-.2393104-.56509654-.5215613-.33323493-.3163366-.44236499-.4185353-.57290215-.533275l-.80130455-.89071892c-.03955779-.05174211-.45812831-.5051399-.5872217-.6688539-.28069963-.35597842-.47062947-.71959073-.56844755-1.14820437-.18921973-.83150113-.1793328-1.21146622-.00855589-1.49112273.13743587-.2257023.43815377-.4195862.60596039-.45241793.17165981-.03465512.55153059-.01648617.62179422.02229321.09902279.05401056.13357243.07300285.16379074.09097645.03572494.02124891.05965747.03799198.08182912.05708809.03426437.02951139.07235014.07170412.12420211.14044502.03611591.04821025.07806642.1053997.1423779.19304882.06054643.0816627.09183576.12069421.13369221.1590035.28038907.25662728.68391532.03238058.65052057-.32606956-.00567036-.06086415-.02203766-.12694598-.05458621-.23708502-.04356824-.15021272.00433013-.05284275-.26002629-.56642281-.08720664-.16942124-.13955864-.28835362-.17428227-.4046158l-.03412852-.10219113c-.03838756-.11059767-.09558223-.26854489-.12612861-.35199347l-.02009957-.05467087.002.008-.05974804-.17751191c-.09232236-.28807194-.13413567-.51358087-.12645475-.72681781.01040781-.28751553.16037753-.54506871.58790983-.70400047.40142488-.1488616 1.07786076.00117106 1.20581167.27856864.04319814.09369738.08927466.21199471.13900415.35457792l.03930997.11680217c.05539717.16759437.13470873.41493582.13860471.42816881.02724222.08344874.0471839.13860719.06943813.18441246.00217869.06301886.00217869.06301886.35429398.23177937.41699479-.29154152.41699479-.29154152.38019201-.37525838.00571063-.08773482.00758408-.17356287.00965287-.37317647.00242546-.23402898.00423842-.33154773.00994479-.45966208.01316411-.29554918.0437926-.51142116.09291227-.63864415.09160418-.23801371.25279279-.40993649.4432431-.46667832.24458613-.07380253.51465245-.09215236.73323569-.04710649zm1.21356228 4.27672201c-.20710459.00095412-.37422255.16961903-.37326843.37672361l.016 3.473c.00095412.20710459.16961903.37422251.37672361.37326841.20710459-.0009541.37422255-.16961901.37326843-.37672359l-.016-3.473c-.00095412-.20710459-.16961903-.37422255-.37672361-.37326843zm2.03332759.00229602c-.2071068 0-.375.16789322-.375.375v3.459c0 .20710678.1678932.375.375.375s.375-.16789322.375-.375v-3.459c0-.20710678-.1678932-.375-.375-.375zm-4.01399856.02930704c-.20710289.00126946-.37396385.17018863-.3726944.37729152l.021 3.426c.00126946.20710289.17018863.37396384.37729152.37269444.20710289-.0012695.37396385-.17018867.3726944-.37729156l-.021-3.426c-.00126946-.20710289-.17018863-.37396385-.37729152-.3726944z",fill:"#fff"})]})})}function T_(){return W.jsxs("svg",{width:"16",height:"16",viewBox:"0 0 20 20",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:[W.jsx("circle",{cx:"10",cy:"10",r:"8",stroke:"rgba(0,0,0,0.15)",strokeWidth:"2"}),W.jsx("path",{d:"M10 2A8 8 0 0 1 18 10",stroke:"black",strokeWidth:"2",strokeLinecap:"round"})]})}const pm="M0-8.4 2.55-3.65H-2.55ZM0 8.4 2.55 3.65H-2.55Z";function ec({turn:s}){return W.jsx("svg",{width:"21",height:"21",viewBox:"-14 -14 28 28",overflow:"visible",children:W.jsxs("g",{transform:`rotate(${s})`,strokeLinejoin:"round",children:[W.jsx("path",{d:pm,style:{fill:"var(--ss-cursor-edge, #fff)",stroke:"var(--ss-cursor-edge, #fff)"},strokeWidth:"3.2"}),W.jsx("path",{d:pm,style:{fill:"var(--ss-cursor-line, #000)",stroke:"var(--ss-cursor-line, #000)"},strokeWidth:"1.2"})]})})}const A_=()=>W.jsx(ec,{turn:0}),R_=()=>W.jsx(ec,{turn:90}),C_=()=>W.jsx(ec,{turn:-45}),b_=()=>W.jsx(ec,{turn:45}),mm={pointer:x_,ibeam:y_,crosshair:S_,hand:M_,open:E_,grab:w_,wait:T_,"resize-ns":A_,"resize-ew":R_,"resize-nwse":C_,"resize-nesw":b_},P_={pointer:{x:7.5,y:5.25},ibeam:{x:5,y:8},crosshair:{x:8.5,y:8.5},hand:{x:9.75,y:3.25},open:{x:11.7,y:10.4},grab:{x:12,y:12},wait:{x:8,y:8},"resize-ns":{x:10.5,y:10.5},"resize-ew":{x:10.5,y:10.5},"resize-nwse":{x:10.5,y:10.5},"resize-nesw":{x:10.5,y:10.5}},L_={x:4,y:3};function D_(){return W.jsx("svg",{width:"22",height:"22",viewBox:"0 0 22 22",className:"ss-cursor__arrow","aria-hidden":!0,children:W.jsx("path",{d:"M4 3 18.5 9.6 11.8 11.8 9.6 18.5Z"})})}function N_({cursorRef:s,style:e="real",kind:t}){return W.jsxs("div",{ref:s,className:"ss-cursor","data-style":e,"data-kind":t,"aria-hidden":!0,children:[e==="touch"&&W.jsx("span",{className:"ss-cursor__streak"}),W.jsxs("div",{className:"ss-cursor__press",children:[(e==="circle"||e==="touch")&&W.jsx("span",{className:"ss-cursor__dot"}),e!=="circle"&&e!=="touch"&&Object.keys(mm).map(r=>{const o=e==="arrow";if(o&&r!=="pointer"&&r!=="ibeam")return null;const l=o&&r==="pointer"?D_:mm[r],u=o&&r==="pointer"?L_:P_[r],f=o&&t!=="ibeam"?"pointer":t;return W.jsx("div",{className:"ss-cursor__glyph","data-glyph":r,"data-active":r===f,style:{marginLeft:-u.x,marginTop:-u.y,transformOrigin:`${u.x}px ${u.y}px`},children:W.jsx(l,{})},r)})]})]})}function I_(s,e){const t=document.createElement("span");t.className="ss-ripple",t.style.left=`${e.x}px`,t.style.top=`${e.y}px`,s.appendChild(t),t.addEventListener("animationend",()=>t.remove())}const U_=Oe.createContext({theme:"light",palette:"accent",fidelity:"standard",layout:"wide"}),D0=Oe.createContext(!1);function ro(){const s=Oe.useContext(D0),[e,t]=Oe.useState(!1);return Oe.useEffect(()=>{const r=window.matchMedia("(prefers-reduced-motion: reduce)"),o=()=>t(r.matches);return o(),r.addEventListener("change",o),()=>r.removeEventListener("change",o)},[]),s||e}const es={now:()=>performance.now(),raf:s=>requestAnimationFrame(s),cancelRaf:s=>cancelAnimationFrame(s),layoutRaf:s=>es.recording?.requestLayoutFrame(s)??requestAnimationFrame(s),cancelLayoutRaf:s=>{const e=es.recording;e?e.cancelLayoutFrame(s):cancelAnimationFrame(s)},timeout:(s,e)=>window.setTimeout(s,e),clearTimeout:s=>window.clearTimeout(s),get recording(){return typeof window>"u"?null:window.__stageshow?.clock??null}},F_={};function tc({width:s,height:e,initial:t=F_,script:r,poster:o,cursor:l,hover:u,play:f="loop",compact:d,keys:p="bottom",palette:v="accent",greys:g,fidelity:_="standard",specimen:S,unframed:M,speed:A=1,accent:y,tokens:x,ground:O,fill:D=!1,theme:R="light",className:z,children:H}){const I=f==="hover"&&typeof window<"u"&&window.matchMedia("(hover: none)").matches?"once":f,[N,C]=Oe.useState("wide"),T=Oe.useRef(N);T.current=N;const F=()=>{const Ne=l.at;return typeof Ne=="object"&&"wide"in Ne?Ne[T.current]:Ne},[$,ee]=Oe.useState(!1),le=N==="compact"&&d?d.width:s,ne=N==="compact"&&d?d.height:e,ce=Oe.useRef(null),re=Oe.useRef(null),V=Oe.useRef(null),me=ro(),ie=!r||me,[P,B]=Oe.useState(()=>ie&&o?o:t),Z=Oe.useRef(P);Z.current=P;const[ue,he]=Oe.useState(1),K=Oe.useRef(1);K.current=ue;const oe=typeof window>"u"?{}:window.__stageshow??{},Ee=A/(oe.slow??1),ye=oe.theme??R,[we,tt]=Oe.useState(l?.kind??"pointer"),at=Ne=>{const qe=re.current;!qe||me||I_(qe,Ne)},U=Oe.useRef(we);U.current=we;const[Me,_e]=Oe.useState({id:0,caps:[],show:!1,down:!1}),[Se,fe]=Oe.useState(null),be=Oe.useRef(Me);be.current=Me;const xe=Oe.useRef({x:0,y:0}),Re=Oe.useRef(null),[ct,ft]=Oe.useState(0),L=Oe.useRef(!1),w=Oe.useRef(!1),J=Oe.useRef(null);Oe.useLayoutEffect(()=>{const Ne=ce.current;if(!Ne)return;const qe=()=>{const Lt=Ne.clientWidth,Wt=!!Ne.parentElement?.closest("[data-ss-wide]"),xn=d&&!Wt&&Lt<d.below?"compact":"wide";C(xn);const un=D||!!Ne.parentElement?.closest("[data-ss-fill]");ee(un);const fn=xn==="compact"?d.width:s,Jt=Math.min(un?2:1,Lt/fn);he(Jt),ft(Math.max(0,(Lt-fn*Jt)/2))};qe();const Mt=new ResizeObserver(qe);Mt.observe(Ne);const vt=new MutationObserver(qe);for(let Lt=Ne.parentElement;Lt;Lt=Lt.parentElement)vt.observe(Lt,{attributes:!0,attributeFilter:["data-ss-wide","data-ss-fill"]});return()=>{Mt.disconnect(),vt.disconnect()}},[s,d?.below,d?.width,D]);const[ge,Ae]=Oe.useState({}),ve=Oe.useCallback(()=>{const Ne=re.current;if(!Ne)return{};const qe={},Mt=Ne.querySelectorAll("[data-target]");if(!Mt.length)return qe;const vt=vd(Ne,K.current);return Mt.forEach(Lt=>{qe[Lt.dataset.target]=f_(Ne,Lt,K.current,vt)}),qe},[]),Je=Oe.useRef({n:0,frame:0,owed:!1}),Le=Oe.useCallback(()=>{const Ne=Je.current;if(Ne.frame||(Ne.frame=es.layoutRaf(()=>{if(Ne.n=0,Ne.frame=0,!Ne.owed)return;Ne.owed=!1;const Mt=ve();Ae(vt=>dm(vt,Mt)?vt:Mt)})),Ne.n>=4){Ne.owed=!0;return}Ne.n++;const qe=ve();Ae(Mt=>dm(Mt,qe)?Mt:qe)},[ve]);Oe.useLayoutEffect(Le),Oe.useLayoutEffect(()=>()=>{es.cancelLayoutRaf(Je.current.frame),Je.current={n:0,frame:0,owed:!1}},[]),Oe.useEffect(()=>{const Ne=re.current;if(Ne)return Ne.addEventListener("transitionend",Le),Ne.addEventListener("animationend",Le),()=>{Ne.removeEventListener("transitionend",Le),Ne.removeEventListener("animationend",Le)}},[Le]);const Ke=Oe.useCallback(Ne=>ge[Ne]??C0,[ge]),[nt,Ie]=Oe.useState(!0);Oe.useLayoutEffect(()=>{Ie(!0);let Ne=!0,qe=0;const Mt=()=>{qe=es.layoutRaf(()=>{qe=es.layoutRaf(()=>Ne&&Ie(!1))})};return!document.fonts||document.fonts.status==="loaded"?Mt():document.fonts.ready.then(()=>Ne&&Mt()),()=>{Ne=!1,es.cancelLayoutRaf(qe)}},[N]);const He=Oe.useRef(0),ut=Oe.useRef(0),Ze=Oe.useRef(!1),Ve=Oe.useRef(null),ht=Oe.useCallback(Ne=>{ut.current&&!Ze.current&&Math.hypot(Ne.x-xe.current.x,Ne.y-xe.current.y)>.5&&(Ze.current=!0,Ve.current??=performance.now()-ut.current),xe.current=Ne,He.current=performance.now();const qe=V.current;qe&&(qe.style.transform=`translate(${Ne.x}px, ${Ne.y}px)`,qe.removeAttribute("data-idle"))},[]),X=Oe.useCallback(Ne=>{typeof Ne=="object"&&Ne!==null&&"wide"in Ne&&(Ne=T.current==="compact"?Ne.compact:Ne.wide);const qe=b0(Ne);if(qe===null)return Ne;const Mt=re.current,vt=Mt?.querySelector(`[data-target="${qe}"]`);if(!Mt||!vt)return $s(`no element with data-target="${qe}"`),xe.current;const Lt=Zo(Mt,vt,K.current),Wt=typeof Ne=="string"?{x:.5,y:.5}:{x:Ne.x??.5,y:Ne.y??.5};return{x:Lt.x+Lt.width*Wt.x,y:Lt.y+Lt.height*Wt.y}},[]);Oe.useLayoutEffect(()=>{if(!ie||!u)return;const Ne=re.current;u.forEach(qe=>Ne?.querySelector(`[data-target="${qe}"]`)?.setAttribute("data-hover",""))}),Oe.useLayoutEffect(()=>{l&&!ut.current&&ht(X(F()))},[ue,N]);const Ue=Oe.useRef(0),ke=Oe.useRef(0),Xe=Oe.useCallback(()=>{++Ue.current,cancelAnimationFrame(ke.current),ke.current=0,re.current?.removeAttribute("data-settling")},[]),De=Oe.useCallback((Ne=!1)=>{Xe();const qe=Ue.current;if(w.current=!1,B(t),tt(l?.kind??"pointer"),_e(vt=>({...vt,show:!1,down:!1})),fe(null),re.current?.querySelectorAll("[data-hover],[data-pressed]").forEach(vt=>{vt.removeAttribute("data-hover"),vt.removeAttribute("data-pressed")}),re.current?.removeAttribute("data-mark"),re.current?.querySelectorAll("[data-scrolled]").forEach(vt=>{vt.scrollTop=0,vt.removeAttribute("data-scrolled"),P0(vt)}),re.current?.querySelectorAll("[data-scrolling]").forEach(vt=>vt.removeAttribute("data-scrolling")),V.current?.removeAttribute("data-pressed"),J.current=null,!l)return;if(!Ne){ke.current=requestAnimationFrame(()=>{ke.current=0,ht(X(F())),Re.current?.(xe.current)});return}const Mt=re.current;Mt?.setAttribute("data-settling",""),ke.current=requestAnimationFrame(()=>{const vt={...xe.current},Lt=X(F()),Wt=js(320+Math.hypot(Lt.x-vt.x,Lt.y-vt.y)*.7,380,700),xn=performance.now(),un=()=>{if(Ue.current!==qe)return;const fn=Math.min(1,(performance.now()-xn)/Wt),Jt=Vl(fn);ht({x:vt.x+(Lt.x-vt.x)*Jt,y:vt.y+(Lt.y-vt.y)*Jt}),fn<1?ke.current=requestAnimationFrame(un):(ke.current=0,Mt?.removeAttribute("data-settling"))};un()})},[N]),Te=Oe.useMemo(()=>Ne=>v_(Ne,{rootRef:re,cursorRef:V,pos:xe,hovered:J,kindRef:U,keysRef:be,dragging:w,autoUsed:L,autoRef:Re,scaleRef:K,speed:Ee,layout:N,cursor:l,resolve:X,place:ht,remeasure:Le,ripple:at,setState:B,setKind:tt,setKeys:_e,setLastKeys:fe}),[X,ht,Ee,N]);Oe.useEffect(()=>{const Ne=re.current;if(ie||!r)return De(),Ne.removeAttribute("data-offscreen"),B(o??t),Xe;De();const qe=ce.current;let Mt=null,vt=!1,Lt=!1,Wt=!1;const xn=l?.idle??4e3,un=1200;let fn=0,Jt=0;const $i=()=>{window.clearInterval(fn),!(!l||xn===!1)&&(He.current=performance.now(),fn=window.setInterval(()=>{const j=V.current;if(!j)return;const ae=performance.now();if(!Ze.current){Ve.current===null&&ae-He.current>un&&j.setAttribute("data-idle","");return}j.hasAttribute("data-pressed")||re.current?.querySelector("[data-hover]")?He.current=ae:ae-He.current>xn&&j.setAttribute("data-idle","")},150))},Ki=()=>{ut.current=performance.now(),Ze.current=!1,window.clearTimeout(Jt);const j=V.current,ae=Ve.current;xn===!1||!j||ae===null||ae<=un||(j.setAttribute("data-idle",""),Jt=window.setTimeout(()=>j.removeAttribute("data-idle"),ae-400))},Zi=()=>{window.clearInterval(fn),window.clearTimeout(Jt),ut.current=0,V.current?.removeAttribute("data-idle")},ls=()=>{window.clearInterval(fn),window.clearTimeout(Jt);const j=V.current,ae=()=>j?.hasAttribute("data-pressed")||Ne.querySelector("[data-hover]");if(!l||xn===!1||!j||j.hasAttribute("data-idle")||ae())return;const pe=(Ze.current?xn:un)-(performance.now()-He.current);Jt=window.setTimeout(()=>{ae()||j.setAttribute("data-idle","")},Math.max(0,pe))},Wn=()=>{if(Mt||Wt||!vt||document.hidden||I==="hover"&&!Lt)return;Xe(),l&&ht(X(F())),Mt=new AbortController;const j=Mt.signal;$i();const ae=Te(j);(async()=>{do{Ki();try{await r(ae)}catch(pe){if(pe instanceof qs)return;console.error("[stageshow] script error",pe),Mt=null,Zi();return}I==="loop"&&L0()&&__(Z.current,t,xe.current,l?X(F()):null)}while(I==="loop"&&!j.aborted);I==="once"&&!j.aborted&&(Wt=!0,ls())})()},Ji=(j=!1)=>{Zi(),Mt&&(Mt.abort(),Mt=null,Wt||De(j))},Qi=()=>Ne.toggleAttribute("data-offscreen",!vt||document.hidden);Qi();const cs=new IntersectionObserver(([j])=>{vt=j.isIntersecting,Qi(),vt?Wn():Ji()});cs.observe(qe);const Pr=()=>{Qi(),document.hidden?Ji():Wn()};document.addEventListener("visibilitychange",Pr);const Lr=()=>{Lt=!0,Wn()},b=()=>{Lt=!1,Ji(!0)};return I==="hover"&&(qe.addEventListener("pointerenter",Lr),qe.addEventListener("pointerleave",b)),()=>{cs.disconnect(),document.removeEventListener("visibilitychange",Pr),qe.removeEventListener("pointerenter",Lr),qe.removeEventListener("pointerleave",b),Zi(),Mt?.abort(),Mt=null,Re.current=null,Xe()}},[ie,r,Te,I,N]),Oe.useLayoutEffect(()=>{l&&!ie&&!w.current&&Re.current?.(xe.current)},[P]);const et=Oe.useMemo(()=>({theme:ye,palette:v,fidelity:_,layout:N}),[ye,v,_,N]),xt=l&&(!r||!ie||l.still);return W.jsx("div",{ref:ce,className:`ss-fit${z?` ${z}`:""}`,style:{maxWidth:$?void 0:s,height:ne*ue},children:W.jsxs("div",{ref:re,className:"ss-stage","data-specimen":S||void 0,"data-unframed":M||void 0,"data-still":ie||void 0,"data-placing":nt||void 0,"data-theme":ye,"data-palette":v,"data-greys":g==="cool"?"cool":void 0,"data-fidelity":_,"data-layout":N,style:{width:le,height:ne,marginLeft:ct||void 0,transform:`scale(${ue})`,...x,...y?{"--ss-accent":y,"--ss-accent-2":y,"--ss-accent-soft":`color-mix(in srgb, ${y} 14%, transparent)`}:null},children:[O&&W.jsx("div",{className:"ss-ground","aria-hidden":!0,style:Array.isArray(O)?{"--ss-orb-1":O[0],"--ss-orb-2":O[1],...O[2]?{"--ss-orb-3":O[2]}:null}:void 0}),W.jsx(D0.Provider,{value:ie,children:W.jsx(U_.Provider,{value:et,children:H(P,Ke,N)})}),r&&W.jsx(c_,{rows:[Se,Me],at:typeof p=="string"?p:p[N]}),xt&&W.jsx(N_,{cursorRef:V,style:l.style,kind:we})]})})}async function O_(s){await s.wait(900),s.mark("file"),await s.set({phase:"flight"}),await s.wait(1e3),s.mark("impact"),await s.set({phase:"impact"}),await s.wait(1500),s.mark("ready"),await s.set({phase:"ready"}),await s.wait(2400)}function k_({theme:s}){const e=Oe.useRef(null);return Oe.useEffect(()=>{const t=window.matchMedia("(prefers-reduced-motion: reduce)"),r=()=>{e.current?.style.setProperty("--rx","-9deg"),e.current?.style.setProperty("--ry","-19deg")},o=l=>{if(t.matches||l.pointerType==="touch"||!e.current)return;const u=e.current.getBoundingClientRect(),f=d=>Math.max(-1,Math.min(1,d));e.current.style.setProperty("--rx",`${-f((l.clientY-u.top-u.height*.5)/u.height)*20}deg`),e.current.style.setProperty("--ry",`${f((l.clientX-u.left-u.width*.58)/u.width)*32}deg`)};return window.addEventListener("pointermove",o,{passive:!0}),document.documentElement.addEventListener("pointerleave",r),t.addEventListener("change",r),()=>{window.removeEventListener("pointermove",o),document.documentElement.removeEventListener("pointerleave",r),t.removeEventListener("change",r)}},[]),W.jsx("div",{ref:e,className:"neo-hero",children:W.jsx(tc,{width:720,height:400,compact:{below:560,width:358,height:340},initial:{phase:"idle"},poster:{phase:"ready"},script:O_,play:"once",theme:s,unframed:!0,className:"neo-stage",children:t=>W.jsxs("div",{className:"neo-scene","data-phase":t.phase,children:[W.jsx("div",{className:"neo-shadow"}),W.jsx("div",{className:"neo-position",children:W.jsx("div",{className:"neo-scale",children:W.jsx("div",{className:"neo-gaze",children:W.jsxs("div",{className:"neo-player",children:[Array.from({length:15},(r,o)=>W.jsx("div",{className:"neo-slice",style:{transform:`translateZ(${o-7}px)`}},o)),W.jsxs("div",{className:"neo-back",children:[W.jsx("span",{children:"Fosi Audio"}),W.jsxs("div",{children:[W.jsx("strong",{children:"DAP Neo"}),W.jsx("small",{children:"Portable Digital Music Player"}),W.jsx("small",{children:"Made in China"})]})]}),W.jsx("div",{className:"neo-side neo-power"}),W.jsx("div",{className:"neo-side neo-volume"}),W.jsx("div",{className:"neo-side neo-next"}),W.jsxs("div",{className:"neo-front",children:[W.jsx("div",{className:"neo-glass",children:W.jsx("div",{className:"neo-display",children:W.jsxs("div",{className:"neo-boot",children:[W.jsx("strong",{children:"CE"}),W.jsx("span",{children:"Community Edition"}),W.jsx("i",{})]})})}),W.jsx("div",{className:"neo-wheel",children:W.jsx("div",{className:"neo-center"})}),W.jsxs("div",{className:"neo-ports",children:[W.jsx("i",{}),W.jsx("b",{}),W.jsx("i",{})]})]})]})})})}),W.jsxs("div",{className:"neo-file","aria-hidden":"true",children:[W.jsx("div",{className:"neo-page",children:W.jsx("span",{children:"IMG"})}),W.jsx("span",{children:"RKNANOFWIMG"})]}),W.jsx("div",{className:"neo-impact","aria-hidden":"true"}),W.jsx("div",{className:"neo-caption",children:"DAP Neo with Community Edition firmware"}),W.jsx("span",{className:"neo-description",children:"An update file hits the player, spins it, and lights its screen with CE."})]})})})}const B_=["var(--ss-ink-1)","var(--ss-ink-2)","var(--ss-ink-3)","var(--ss-ink-4)","var(--ss-ink-5)"];function Bu({w:s,h:e=6,tone:t=3,r=2,shrink:o,className:l,style:u,...f}){const d=o??(typeof s=="number"&&s>e*3);return W.jsx("span",{...f,className:`ss-bar${l?` ${l}`:""}`,"data-shrink":d||void 0,style:{width:s,height:e,borderRadius:r,background:B_[t-1],...u}})}const z_="012345678901234567890123456789".split(""),dl=10,H_=s=>{const e=/^(.*\d)(\s*)([^\d\s.,]+)$/.exec(s);return e?{head:e[1],space:e[2].length>0,unit:e[3]}:{head:s,space:!1,unit:""}},gm=s=>{const e=[];for(let t=s.length-1;t>=0;t--){const r=s[t];r>="0"&&r<="9"&&e.push(Number(r))}return e};function V_({value:s,format:e=f=>Math.round(f).toLocaleString("en-US"),duration:t=700,stagger:r=45,className:o,style:l,...u}){const f=ro(),d=Oe.useRef(null),p=e(s),{head:v,space:g,unit:_}=H_(p),S=v.split(""),M=gm(p),[A,y]=Oe.useState(()=>M.map(R=>dl+R)),x=Oe.useRef({text:p,value:s,idx:A});x.current.idx=A;const O=Oe.useRef(!1);Oe.useLayoutEffect(()=>{const R=d.current;if(!R)return;const z=x.current;if(z.text===p)return;const H=f||t<=0||!!R.closest("[data-instant], [data-offscreen]"),I=gm(z.text),N=s>=z.value,C=M.map((T,F)=>{const $=I[F],ee=z.idx[F];return $===void 0||ee===void 0||H?dl+T:$===T?ee:N?ee+(T-$+10)%10:ee-($-T+10)%10});if(R.toggleAttribute("data-snap",H),!H){for(const T of Array.from(R.querySelectorAll(".ss-count__strip")))getComputedStyle(T).transform;R.setAttribute("data-rolling","")}x.current={text:p,value:s,idx:C},y(C)},[p,s,f,t]),Oe.useEffect(()=>{const R=d.current;if(!R||!R.hasAttribute("data-rolling"))return;const z=window.setTimeout(()=>{R.setAttribute("data-snap",""),O.current=!0;const H=M.map(I=>dl+I);x.current.idx=H,y(H),R.removeAttribute("data-rolling")},t+r*M.length+60);return()=>window.clearTimeout(z)},[A]),Oe.useLayoutEffect(()=>{const R=d.current;if(!(!R||!O.current)){O.current=!1;for(const z of Array.from(R.querySelectorAll(".ss-count__strip")))getComputedStyle(z).transform;R.removeAttribute("data-snap")}},[A]);let D=M.length;return W.jsxs("span",{...u,ref:d,className:`ss-count${o?` ${o}`:""}`,style:l,"aria-label":p,children:[S.map((R,z)=>{if(R<"0"||R>"9")return W.jsx("span",{className:"ss-count__char","aria-hidden":!0,children:R},`s${z}-${R}`);const H=--D,I=A[H]??dl+Number(R);return W.jsx("span",{className:"ss-count__digit","data-crop":!0,"aria-hidden":!0,children:W.jsx("span",{className:"ss-count__strip",style:{transform:`translateY(${-I}em)`,transitionDuration:`${t}ms`,transitionDelay:`${H*r}ms`},children:z_.map((N,C)=>W.jsx("span",{children:N},C))})},`d${H}`)}),_&&W.jsx("span",{className:"ss-count__unit","data-space":g||void 0,"aria-hidden":!0,children:_})]})}function G_({delay:s=0,children:e,...t}){const r=ro(),[o,l]=Oe.useState(e);return Oe.useEffect(()=>{if(!s||r)return l(e);const u=setTimeout(()=>l(e),s);return()=>clearTimeout(u)},[e,s,r]),W.jsx(W_,{...t,children:s&&!r?o:e})}function W_({children:s,stagger:e=45,variant:t="roll",align:r,className:o,style:l}){const u=ro(),[f,d]=Oe.useState({text:s,head:0,tail:0,old:"",key:0,numeric:!0}),p=Oe.useRef(null),v=Oe.useRef(null),g=Oe.useRef(null),_=()=>{if(!v.current||!p.current)return 0;const I=parseFloat(getComputedStyle(p.current).height),N=I>0?p.current.getBoundingClientRect().height/I:1;return v.current.getBoundingClientRect().width/(N||1)},[S,M]=Oe.useState(r??"start");Oe.useLayoutEffect(()=>{if(r)return M(r);const I=v.current;if(!I?.parentElement)return;let N=I;for(;N.parentElement&&N.parentElement.childElementCount===1&&Math.abs(N.parentElement.getBoundingClientRect().width-N.getBoundingClientRect().width)<1;)N=N.parentElement;const C=N.parentElement;if(!C)return;const T=getComputedStyle(C),F=/flex/.test(T.display)&&T.flexDirection.startsWith("row"),$=()=>{const le=N.previousElementSibling,ne=N.getBoundingClientRect(),ce=C.getBoundingClientRect(),re=Math.abs(ce.right-parseFloat(T.paddingRight)-parseFloat(T.borderRightWidth)-ne.right)<1,V=le?ne.left-le.getBoundingClientRect().right-(parseFloat(T.columnGap)||0):0;return re&&V>1},ee=/right|end/.test(getComputedStyle(I).textAlign)||F&&N===C.lastElementChild&&(/space-between|flex-end|^end/.test(T.justifyContent)||$());M(ee?"end":"start")},[r]),Oe.useEffect(()=>{if(u){d({text:s,head:0,tail:0,old:"",key:0,numeric:!0});return}if(f.text===s)return;const I=f.text,N=s;let C=0;for(;C<I.length&&C<N.length&&I[C]===N[C];)C++;let T=0;for(;T<I.length-C&&T<N.length-C&&I[I.length-1-T]===N[N.length-1-T];)T++;const F=/^[\d.,$€£%+\-−\s]*$/.test(I.slice(C,I.length-T)+N.slice(C,N.length-T));if(!F){const le=ne=>ne===void 0||/\s/.test(ne);for(;C>0&&!le(N[C-1])&&!le(N[C]);)C--;for(;T>0&&!le(N[N.length-T-1])&&!le(N[N.length-T]);)T--}const $=f.key+1;g.current=_(),d({text:N,head:C,tail:T,old:I.slice(C,I.length-T),key:$,numeric:F});const ee=setTimeout(()=>d(le=>le.key===$?{...le,old:""}:le),700);return()=>clearTimeout(ee)},[s,u]),Oe.useLayoutEffect(()=>{const I=p.current,N=I?.querySelector("[data-live]"),C=I?.querySelector("[data-out]");if(!I||!N)return;const T=re=>parseFloat(getComputedStyle(re).width)||0,F=T(N);if(u||f.key===0){I.style.transition="none",I.style.width=`${F}px`,g.current=null;return}const $=_()-T(I),ee=g.current;g.current=null;const le=ee===null?C?T(C):0:Math.max(0,ee-$);if(I.style.transition="none",I.style.width=`${le}px`,I.offsetWidth,I.style.transition="",t==="fade"){I.style.width=`${F}px`;return}const ne=Math.max(F,le,C?T(C):0);if(I.style.width=`${ne}px`,ne===F)return;const ce=setTimeout(()=>I.style.width=`${F}px`,360);return()=>clearTimeout(ce)},[f.key,u,u?s:void 0]);const{text:A,head:y,tail:x,old:O,key:D,numeric:R}=u?{text:s,head:0,tail:0,old:"",key:0,numeric:!0}:f,z=A.slice(y,A.length-x),H=R?z.split(""):z.split(/(?<=\s)/);return W.jsxs("span",{ref:v,className:`ss-roll${o?` ${o}`:""}`,"data-variant":t,"data-align":S,style:l,children:[A.slice(0,y),W.jsxs("span",{ref:p,className:"ss-roll__mid",children:[O&&W.jsx("span",{className:"ss-roll__item","data-out":!0,children:O},`o${D}`),W.jsx("span",{className:"ss-roll__item","data-live":!0,children:D>0&&t==="fade"?W.jsx("span",{className:"ss-roll__char",children:z}):D>0?H.map((I,N)=>W.jsx("span",{className:"ss-roll__char",style:{animationDelay:`${N*e}ms`},children:I},N)):z},`n${D}`)]}),A.slice(A.length-x)]})}function X_({value:s,states:e,align:t="center",className:r,style:o,...l}){const u=ro();return W.jsx("span",{...l,className:`ss-states${r?` ${r}`:""}`,"data-align":t,"data-reduced":u||void 0,style:o,children:Object.keys(e).map(f=>W.jsx("span",{className:"ss-states__item","data-on":f===s||void 0,"aria-hidden":f!==s||void 0,children:e[f]},f))})}function N0({pad:s="medium",gap:e=12,tone:t="surface",lift:r,flush:o,className:l,style:u,...f}){return W.jsx("div",{...f,className:`ss-card${l?` ${l}`:""}`,"data-pad":s,"data-tone":t,"data-lift":r||void 0,"data-flush":o||void 0,style:{...u,"--ss-card-gap":`${e}px`}})}function hl({variant:s="secondary",size:e="medium",icon:t,trailingIcon:r,children:o,className:l,...u}){const[f,d]=Oe.useState(t),[p,v]=Oe.useState(!!t),g=!!t;return Oe.useLayoutEffect(()=>{if(!g)return v(!1);if(d(t),p)return;const _=requestAnimationFrame(()=>v(!0));return()=>cancelAnimationFrame(_)},[g]),W.jsxs("span",{role:"button","data-cursor":"pointer",...u,className:`ss-button${l?` ${l}`:""}`,"data-variant":s,"data-size":e,"data-leading":p?"":void 0,"data-trailing":r?"":void 0,children:[f!=null&&W.jsx("span",{className:"ss-button__icon ss-button__lead","data-open":p||void 0,onTransitionEnd:_=>{!g&&_.propertyName==="width"&&d(null)},children:t??f}),o!=null&&o!==!1&&W.jsx("span",{className:"ss-button__label",children:typeof o=="string"||typeof o=="number"?W.jsx(G_,{variant:"fade",children:String(o)}):o}),r&&W.jsx("span",{className:"ss-button__icon",children:r})]})}/**
 * @license
 * Copyright 2010-2025 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const _d="180",j_=0,vm=1,q_=2,I0=1,Y_=2,Gi=3,Cr=0,Gn=1,Wi=2,Ar=0,Ks=1,_m=2,xm=3,ym=4,$_=5,ts=100,K_=101,Z_=102,J_=103,Q_=104,ex=200,tx=201,nx=202,ix=203,Mf=204,Ef=205,rx=206,sx=207,ox=208,ax=209,lx=210,cx=211,ux=212,fx=213,dx=214,wf=0,Tf=1,Af=2,Js=3,Rf=4,Cf=5,bf=6,Pf=7,U0=0,hx=1,px=2,Rr=0,mx=1,gx=2,vx=3,_x=4,xx=5,yx=6,Sx=7,F0=300,Qs=301,eo=302,Lf=303,Df=304,nc=306,Nf=1e3,is=1001,If=1002,vi=1003,Mx=1004,pl=1005,Ei=1006,zu=1007,rs=1008,Ai=1009,O0=1010,k0=1011,Jo=1012,xd=1013,ss=1014,Xi=1015,oa=1016,yd=1017,Sd=1018,Qo=1020,B0=35902,z0=35899,H0=1021,V0=1022,gi=1023,ea=1026,ta=1027,G0=1028,Md=1029,W0=1030,Ed=1031,wd=1033,Gl=33776,Wl=33777,Xl=33778,jl=33779,Uf=35840,Ff=35841,Of=35842,kf=35843,Bf=36196,zf=37492,Hf=37496,Vf=37808,Gf=37809,Wf=37810,Xf=37811,jf=37812,qf=37813,Yf=37814,$f=37815,Kf=37816,Zf=37817,Jf=37818,Qf=37819,ed=37820,td=37821,nd=36492,id=36494,rd=36495,sd=36283,od=36284,ad=36285,ld=36286,Ex=3200,wx=3201,X0=0,Tx=1,Tr="",Vn="srgb",to="srgb-linear",$l="linear",kt="srgb",Ds=7680,Sm=519,Ax=512,Rx=513,Cx=514,j0=515,bx=516,Px=517,Lx=518,Dx=519,Mm=35044,Em="300 es",wi=2e3,Kl=2001;class so{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const r=this._listeners;r[e]===void 0&&(r[e]=[]),r[e].indexOf(t)===-1&&r[e].push(t)}hasEventListener(e,t){const r=this._listeners;return r===void 0?!1:r[e]!==void 0&&r[e].indexOf(t)!==-1}removeEventListener(e,t){const r=this._listeners;if(r===void 0)return;const o=r[e];if(o!==void 0){const l=o.indexOf(t);l!==-1&&o.splice(l,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const r=t[e.type];if(r!==void 0){e.target=this;const o=r.slice(0);for(let l=0,u=o.length;l<u;l++)o[l].call(this,e);e.target=null}}}const An=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Hu=Math.PI/180,cd=180/Math.PI;function oo(){const s=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,r=Math.random()*4294967295|0;return(An[s&255]+An[s>>8&255]+An[s>>16&255]+An[s>>24&255]+"-"+An[e&255]+An[e>>8&255]+"-"+An[e>>16&15|64]+An[e>>24&255]+"-"+An[t&63|128]+An[t>>8&255]+"-"+An[t>>16&255]+An[t>>24&255]+An[r&255]+An[r>>8&255]+An[r>>16&255]+An[r>>24&255]).toLowerCase()}function Ct(s,e,t){return Math.max(e,Math.min(t,s))}function Nx(s,e){return(s%e+e)%e}function Vu(s,e,t){return(1-t)*s+t*e}function Ho(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return s/4294967295;case Uint16Array:return s/65535;case Uint8Array:return s/255;case Int32Array:return Math.max(s/2147483647,-1);case Int16Array:return Math.max(s/32767,-1);case Int8Array:return Math.max(s/127,-1);default:throw new Error("Invalid component type.")}}function Hn(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return Math.round(s*4294967295);case Uint16Array:return Math.round(s*65535);case Uint8Array:return Math.round(s*255);case Int32Array:return Math.round(s*2147483647);case Int16Array:return Math.round(s*32767);case Int8Array:return Math.round(s*127);default:throw new Error("Invalid component type.")}}class Ge{constructor(e=0,t=0){Ge.prototype.isVector2=!0,this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,r=this.y,o=e.elements;return this.x=o[0]*t+o[3]*r+o[6],this.y=o[1]*t+o[4]*r+o[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Ct(this.x,e.x,t.x),this.y=Ct(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Ct(this.x,e,t),this.y=Ct(this.y,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ct(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const r=this.dot(e)/t;return Math.acos(Ct(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,r=this.y-e.y;return t*t+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const r=Math.cos(t),o=Math.sin(t),l=this.x-e.x,u=this.y-e.y;return this.x=l*r-u*o+e.x,this.y=l*o+u*r+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class aa{constructor(e=0,t=0,r=0,o=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=r,this._w=o}static slerpFlat(e,t,r,o,l,u,f){let d=r[o+0],p=r[o+1],v=r[o+2],g=r[o+3];const _=l[u+0],S=l[u+1],M=l[u+2],A=l[u+3];if(f===0){e[t+0]=d,e[t+1]=p,e[t+2]=v,e[t+3]=g;return}if(f===1){e[t+0]=_,e[t+1]=S,e[t+2]=M,e[t+3]=A;return}if(g!==A||d!==_||p!==S||v!==M){let y=1-f;const x=d*_+p*S+v*M+g*A,O=x>=0?1:-1,D=1-x*x;if(D>Number.EPSILON){const z=Math.sqrt(D),H=Math.atan2(z,x*O);y=Math.sin(y*H)/z,f=Math.sin(f*H)/z}const R=f*O;if(d=d*y+_*R,p=p*y+S*R,v=v*y+M*R,g=g*y+A*R,y===1-f){const z=1/Math.sqrt(d*d+p*p+v*v+g*g);d*=z,p*=z,v*=z,g*=z}}e[t]=d,e[t+1]=p,e[t+2]=v,e[t+3]=g}static multiplyQuaternionsFlat(e,t,r,o,l,u){const f=r[o],d=r[o+1],p=r[o+2],v=r[o+3],g=l[u],_=l[u+1],S=l[u+2],M=l[u+3];return e[t]=f*M+v*g+d*S-p*_,e[t+1]=d*M+v*_+p*g-f*S,e[t+2]=p*M+v*S+f*_-d*g,e[t+3]=v*M-f*g-d*_-p*S,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,r,o){return this._x=e,this._y=t,this._z=r,this._w=o,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const r=e._x,o=e._y,l=e._z,u=e._order,f=Math.cos,d=Math.sin,p=f(r/2),v=f(o/2),g=f(l/2),_=d(r/2),S=d(o/2),M=d(l/2);switch(u){case"XYZ":this._x=_*v*g+p*S*M,this._y=p*S*g-_*v*M,this._z=p*v*M+_*S*g,this._w=p*v*g-_*S*M;break;case"YXZ":this._x=_*v*g+p*S*M,this._y=p*S*g-_*v*M,this._z=p*v*M-_*S*g,this._w=p*v*g+_*S*M;break;case"ZXY":this._x=_*v*g-p*S*M,this._y=p*S*g+_*v*M,this._z=p*v*M+_*S*g,this._w=p*v*g-_*S*M;break;case"ZYX":this._x=_*v*g-p*S*M,this._y=p*S*g+_*v*M,this._z=p*v*M-_*S*g,this._w=p*v*g+_*S*M;break;case"YZX":this._x=_*v*g+p*S*M,this._y=p*S*g+_*v*M,this._z=p*v*M-_*S*g,this._w=p*v*g-_*S*M;break;case"XZY":this._x=_*v*g-p*S*M,this._y=p*S*g-_*v*M,this._z=p*v*M+_*S*g,this._w=p*v*g+_*S*M;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+u)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const r=t/2,o=Math.sin(r);return this._x=e.x*o,this._y=e.y*o,this._z=e.z*o,this._w=Math.cos(r),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,r=t[0],o=t[4],l=t[8],u=t[1],f=t[5],d=t[9],p=t[2],v=t[6],g=t[10],_=r+f+g;if(_>0){const S=.5/Math.sqrt(_+1);this._w=.25/S,this._x=(v-d)*S,this._y=(l-p)*S,this._z=(u-o)*S}else if(r>f&&r>g){const S=2*Math.sqrt(1+r-f-g);this._w=(v-d)/S,this._x=.25*S,this._y=(o+u)/S,this._z=(l+p)/S}else if(f>g){const S=2*Math.sqrt(1+f-r-g);this._w=(l-p)/S,this._x=(o+u)/S,this._y=.25*S,this._z=(d+v)/S}else{const S=2*Math.sqrt(1+g-r-f);this._w=(u-o)/S,this._x=(l+p)/S,this._y=(d+v)/S,this._z=.25*S}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let r=e.dot(t)+1;return r<1e-8?(r=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=r):(this._x=0,this._y=-e.z,this._z=e.y,this._w=r)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=r),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Ct(this.dot(e),-1,1)))}rotateTowards(e,t){const r=this.angleTo(e);if(r===0)return this;const o=Math.min(1,t/r);return this.slerp(e,o),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const r=e._x,o=e._y,l=e._z,u=e._w,f=t._x,d=t._y,p=t._z,v=t._w;return this._x=r*v+u*f+o*p-l*d,this._y=o*v+u*d+l*f-r*p,this._z=l*v+u*p+r*d-o*f,this._w=u*v-r*f-o*d-l*p,this._onChangeCallback(),this}slerp(e,t){if(t===0)return this;if(t===1)return this.copy(e);const r=this._x,o=this._y,l=this._z,u=this._w;let f=u*e._w+r*e._x+o*e._y+l*e._z;if(f<0?(this._w=-e._w,this._x=-e._x,this._y=-e._y,this._z=-e._z,f=-f):this.copy(e),f>=1)return this._w=u,this._x=r,this._y=o,this._z=l,this;const d=1-f*f;if(d<=Number.EPSILON){const S=1-t;return this._w=S*u+t*this._w,this._x=S*r+t*this._x,this._y=S*o+t*this._y,this._z=S*l+t*this._z,this.normalize(),this}const p=Math.sqrt(d),v=Math.atan2(p,f),g=Math.sin((1-t)*v)/p,_=Math.sin(t*v)/p;return this._w=u*g+this._w*_,this._x=r*g+this._x*_,this._y=o*g+this._y*_,this._z=l*g+this._z*_,this._onChangeCallback(),this}slerpQuaternions(e,t,r){return this.copy(e).slerp(t,r)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),r=Math.random(),o=Math.sqrt(1-r),l=Math.sqrt(r);return this.set(o*Math.sin(e),o*Math.cos(e),l*Math.sin(t),l*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class Q{constructor(e=0,t=0,r=0){Q.prototype.isVector3=!0,this.x=e,this.y=t,this.z=r}set(e,t,r){return r===void 0&&(r=this.z),this.x=e,this.y=t,this.z=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(wm.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(wm.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,r=this.y,o=this.z,l=e.elements;return this.x=l[0]*t+l[3]*r+l[6]*o,this.y=l[1]*t+l[4]*r+l[7]*o,this.z=l[2]*t+l[5]*r+l[8]*o,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,r=this.y,o=this.z,l=e.elements,u=1/(l[3]*t+l[7]*r+l[11]*o+l[15]);return this.x=(l[0]*t+l[4]*r+l[8]*o+l[12])*u,this.y=(l[1]*t+l[5]*r+l[9]*o+l[13])*u,this.z=(l[2]*t+l[6]*r+l[10]*o+l[14])*u,this}applyQuaternion(e){const t=this.x,r=this.y,o=this.z,l=e.x,u=e.y,f=e.z,d=e.w,p=2*(u*o-f*r),v=2*(f*t-l*o),g=2*(l*r-u*t);return this.x=t+d*p+u*g-f*v,this.y=r+d*v+f*p-l*g,this.z=o+d*g+l*v-u*p,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,r=this.y,o=this.z,l=e.elements;return this.x=l[0]*t+l[4]*r+l[8]*o,this.y=l[1]*t+l[5]*r+l[9]*o,this.z=l[2]*t+l[6]*r+l[10]*o,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Ct(this.x,e.x,t.x),this.y=Ct(this.y,e.y,t.y),this.z=Ct(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Ct(this.x,e,t),this.y=Ct(this.y,e,t),this.z=Ct(this.z,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ct(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this.z=e.z+(t.z-e.z)*r,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const r=e.x,o=e.y,l=e.z,u=t.x,f=t.y,d=t.z;return this.x=o*d-l*f,this.y=l*u-r*d,this.z=r*f-o*u,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const r=e.dot(this)/t;return this.copy(e).multiplyScalar(r)}projectOnPlane(e){return Gu.copy(this).projectOnVector(e),this.sub(Gu)}reflect(e){return this.sub(Gu.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const r=this.dot(e)/t;return Math.acos(Ct(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,r=this.y-e.y,o=this.z-e.z;return t*t+r*r+o*o}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,r){const o=Math.sin(t)*e;return this.x=o*Math.sin(r),this.y=Math.cos(t)*e,this.z=o*Math.cos(r),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,r){return this.x=e*Math.sin(t),this.y=r,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),r=this.setFromMatrixColumn(e,1).length(),o=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=r,this.z=o,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,r=Math.sqrt(1-t*t);return this.x=r*Math.cos(e),this.y=t,this.z=r*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}const Gu=new Q,wm=new aa;class Et{constructor(e,t,r,o,l,u,f,d,p){Et.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,r,o,l,u,f,d,p)}set(e,t,r,o,l,u,f,d,p){const v=this.elements;return v[0]=e,v[1]=o,v[2]=f,v[3]=t,v[4]=l,v[5]=d,v[6]=r,v[7]=u,v[8]=p,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,r=e.elements;return t[0]=r[0],t[1]=r[1],t[2]=r[2],t[3]=r[3],t[4]=r[4],t[5]=r[5],t[6]=r[6],t[7]=r[7],t[8]=r[8],this}extractBasis(e,t,r){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),r.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const r=e.elements,o=t.elements,l=this.elements,u=r[0],f=r[3],d=r[6],p=r[1],v=r[4],g=r[7],_=r[2],S=r[5],M=r[8],A=o[0],y=o[3],x=o[6],O=o[1],D=o[4],R=o[7],z=o[2],H=o[5],I=o[8];return l[0]=u*A+f*O+d*z,l[3]=u*y+f*D+d*H,l[6]=u*x+f*R+d*I,l[1]=p*A+v*O+g*z,l[4]=p*y+v*D+g*H,l[7]=p*x+v*R+g*I,l[2]=_*A+S*O+M*z,l[5]=_*y+S*D+M*H,l[8]=_*x+S*R+M*I,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],r=e[1],o=e[2],l=e[3],u=e[4],f=e[5],d=e[6],p=e[7],v=e[8];return t*u*v-t*f*p-r*l*v+r*f*d+o*l*p-o*u*d}invert(){const e=this.elements,t=e[0],r=e[1],o=e[2],l=e[3],u=e[4],f=e[5],d=e[6],p=e[7],v=e[8],g=v*u-f*p,_=f*d-v*l,S=p*l-u*d,M=t*g+r*_+o*S;if(M===0)return this.set(0,0,0,0,0,0,0,0,0);const A=1/M;return e[0]=g*A,e[1]=(o*p-v*r)*A,e[2]=(f*r-o*u)*A,e[3]=_*A,e[4]=(v*t-o*d)*A,e[5]=(o*l-f*t)*A,e[6]=S*A,e[7]=(r*d-p*t)*A,e[8]=(u*t-r*l)*A,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,r,o,l,u,f){const d=Math.cos(l),p=Math.sin(l);return this.set(r*d,r*p,-r*(d*u+p*f)+u+e,-o*p,o*d,-o*(-p*u+d*f)+f+t,0,0,1),this}scale(e,t){return this.premultiply(Wu.makeScale(e,t)),this}rotate(e){return this.premultiply(Wu.makeRotation(-e)),this}translate(e,t){return this.premultiply(Wu.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,-r,0,r,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,r=e.elements;for(let o=0;o<9;o++)if(t[o]!==r[o])return!1;return!0}fromArray(e,t=0){for(let r=0;r<9;r++)this.elements[r]=e[r+t];return this}toArray(e=[],t=0){const r=this.elements;return e[t]=r[0],e[t+1]=r[1],e[t+2]=r[2],e[t+3]=r[3],e[t+4]=r[4],e[t+5]=r[5],e[t+6]=r[6],e[t+7]=r[7],e[t+8]=r[8],e}clone(){return new this.constructor().fromArray(this.elements)}}const Wu=new Et;function q0(s){for(let e=s.length-1;e>=0;--e)if(s[e]>=65535)return!0;return!1}function Zl(s){return document.createElementNS("http://www.w3.org/1999/xhtml",s)}function Ix(){const s=Zl("canvas");return s.style.display="block",s}const Tm={};function na(s){s in Tm||(Tm[s]=!0,console.warn(s))}function Ux(s,e,t){return new Promise(function(r,o){function l(){switch(s.clientWaitSync(e,s.SYNC_FLUSH_COMMANDS_BIT,0)){case s.WAIT_FAILED:o();break;case s.TIMEOUT_EXPIRED:setTimeout(l,t);break;default:r()}}setTimeout(l,t)})}const Am=new Et().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Rm=new Et().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Fx(){const s={enabled:!0,workingColorSpace:to,spaces:{},convert:function(o,l,u){return this.enabled===!1||l===u||!l||!u||(this.spaces[l].transfer===kt&&(o.r=Yi(o.r),o.g=Yi(o.g),o.b=Yi(o.b)),this.spaces[l].primaries!==this.spaces[u].primaries&&(o.applyMatrix3(this.spaces[l].toXYZ),o.applyMatrix3(this.spaces[u].fromXYZ)),this.spaces[u].transfer===kt&&(o.r=Zs(o.r),o.g=Zs(o.g),o.b=Zs(o.b))),o},workingToColorSpace:function(o,l){return this.convert(o,this.workingColorSpace,l)},colorSpaceToWorking:function(o,l){return this.convert(o,l,this.workingColorSpace)},getPrimaries:function(o){return this.spaces[o].primaries},getTransfer:function(o){return o===Tr?$l:this.spaces[o].transfer},getToneMappingMode:function(o){return this.spaces[o].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(o,l=this.workingColorSpace){return o.fromArray(this.spaces[l].luminanceCoefficients)},define:function(o){Object.assign(this.spaces,o)},_getMatrix:function(o,l,u){return o.copy(this.spaces[l].toXYZ).multiply(this.spaces[u].fromXYZ)},_getDrawingBufferColorSpace:function(o){return this.spaces[o].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(o=this.workingColorSpace){return this.spaces[o].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(o,l){return na("THREE.ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),s.workingToColorSpace(o,l)},toWorkingColorSpace:function(o,l){return na("THREE.ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),s.colorSpaceToWorking(o,l)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],r=[.3127,.329];return s.define({[to]:{primaries:e,whitePoint:r,transfer:$l,toXYZ:Am,fromXYZ:Rm,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Vn},outputColorSpaceConfig:{drawingBufferColorSpace:Vn}},[Vn]:{primaries:e,whitePoint:r,transfer:kt,toXYZ:Am,fromXYZ:Rm,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Vn}}}),s}const Nt=Fx();function Yi(s){return s<.04045?s*.0773993808:Math.pow(s*.9478672986+.0521327014,2.4)}function Zs(s){return s<.0031308?s*12.92:1.055*Math.pow(s,.41666)-.055}let Ns;class Ox{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let r;if(e instanceof HTMLCanvasElement)r=e;else{Ns===void 0&&(Ns=Zl("canvas")),Ns.width=e.width,Ns.height=e.height;const o=Ns.getContext("2d");e instanceof ImageData?o.putImageData(e,0,0):o.drawImage(e,0,0,e.width,e.height),r=Ns}return r.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=Zl("canvas");t.width=e.width,t.height=e.height;const r=t.getContext("2d");r.drawImage(e,0,0,e.width,e.height);const o=r.getImageData(0,0,e.width,e.height),l=o.data;for(let u=0;u<l.length;u++)l[u]=Yi(l[u]/255)*255;return r.putImageData(o,0,0),t}else if(e.data){const t=e.data.slice(0);for(let r=0;r<t.length;r++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[r]=Math.floor(Yi(t[r]/255)*255):t[r]=Yi(t[r]);return{data:t,width:e.width,height:e.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let kx=0;class Td{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:kx++}),this.uuid=oo(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):t instanceof VideoFrame?e.set(t.displayHeight,t.displayWidth,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const r={uuid:this.uuid,url:""},o=this.data;if(o!==null){let l;if(Array.isArray(o)){l=[];for(let u=0,f=o.length;u<f;u++)o[u].isDataTexture?l.push(Xu(o[u].image)):l.push(Xu(o[u]))}else l=Xu(o);r.url=l}return t||(e.images[this.uuid]=r),r}}function Xu(s){return typeof HTMLImageElement<"u"&&s instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&s instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&s instanceof ImageBitmap?Ox.getDataURL(s):s.data?{data:Array.from(s.data),width:s.width,height:s.height,type:s.data.constructor.name}:(console.warn("THREE.Texture: Unable to serialize Texture."),{})}let Bx=0;const ju=new Q;class Nn extends so{constructor(e=Nn.DEFAULT_IMAGE,t=Nn.DEFAULT_MAPPING,r=is,o=is,l=Ei,u=rs,f=gi,d=Ai,p=Nn.DEFAULT_ANISOTROPY,v=Tr){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Bx++}),this.uuid=oo(),this.name="",this.source=new Td(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=r,this.wrapT=o,this.magFilter=l,this.minFilter=u,this.anisotropy=p,this.format=f,this.internalFormat=null,this.type=d,this.offset=new Ge(0,0),this.repeat=new Ge(1,1),this.center=new Ge(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Et,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=v,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0}get width(){return this.source.getSize(ju).x}get height(){return this.source.getSize(ju).y}get depth(){return this.source.getSize(ju).z}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const r=e[t];if(r===void 0){console.warn(`THREE.Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const o=this[t];if(o===void 0){console.warn(`THREE.Texture.setValues(): property '${t}' does not exist.`);continue}o&&r&&o.isVector2&&r.isVector2||o&&r&&o.isVector3&&r.isVector3||o&&r&&o.isMatrix3&&r.isMatrix3?o.copy(r):this[t]=r}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const r={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(r.userData=this.userData),t||(e.textures[this.uuid]=r),r}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==F0)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Nf:e.x=e.x-Math.floor(e.x);break;case is:e.x=e.x<0?0:1;break;case If:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Nf:e.y=e.y-Math.floor(e.y);break;case is:e.y=e.y<0?0:1;break;case If:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Nn.DEFAULT_IMAGE=null;Nn.DEFAULT_MAPPING=F0;Nn.DEFAULT_ANISOTROPY=1;class Zt{constructor(e=0,t=0,r=0,o=1){Zt.prototype.isVector4=!0,this.x=e,this.y=t,this.z=r,this.w=o}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,r,o){return this.x=e,this.y=t,this.z=r,this.w=o,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,r=this.y,o=this.z,l=this.w,u=e.elements;return this.x=u[0]*t+u[4]*r+u[8]*o+u[12]*l,this.y=u[1]*t+u[5]*r+u[9]*o+u[13]*l,this.z=u[2]*t+u[6]*r+u[10]*o+u[14]*l,this.w=u[3]*t+u[7]*r+u[11]*o+u[15]*l,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,r,o,l;const d=e.elements,p=d[0],v=d[4],g=d[8],_=d[1],S=d[5],M=d[9],A=d[2],y=d[6],x=d[10];if(Math.abs(v-_)<.01&&Math.abs(g-A)<.01&&Math.abs(M-y)<.01){if(Math.abs(v+_)<.1&&Math.abs(g+A)<.1&&Math.abs(M+y)<.1&&Math.abs(p+S+x-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const D=(p+1)/2,R=(S+1)/2,z=(x+1)/2,H=(v+_)/4,I=(g+A)/4,N=(M+y)/4;return D>R&&D>z?D<.01?(r=0,o=.707106781,l=.707106781):(r=Math.sqrt(D),o=H/r,l=I/r):R>z?R<.01?(r=.707106781,o=0,l=.707106781):(o=Math.sqrt(R),r=H/o,l=N/o):z<.01?(r=.707106781,o=.707106781,l=0):(l=Math.sqrt(z),r=I/l,o=N/l),this.set(r,o,l,t),this}let O=Math.sqrt((y-M)*(y-M)+(g-A)*(g-A)+(_-v)*(_-v));return Math.abs(O)<.001&&(O=1),this.x=(y-M)/O,this.y=(g-A)/O,this.z=(_-v)/O,this.w=Math.acos((p+S+x-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Ct(this.x,e.x,t.x),this.y=Ct(this.y,e.y,t.y),this.z=Ct(this.z,e.z,t.z),this.w=Ct(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Ct(this.x,e,t),this.y=Ct(this.y,e,t),this.z=Ct(this.z,e,t),this.w=Ct(this.w,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ct(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this.z=e.z+(t.z-e.z)*r,this.w=e.w+(t.w-e.w)*r,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class zx extends so{constructor(e=1,t=1,r={}){super(),r=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Ei,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},r),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=r.depth,this.scissor=new Zt(0,0,e,t),this.scissorTest=!1,this.viewport=new Zt(0,0,e,t);const o={width:e,height:t,depth:r.depth},l=new Nn(o);this.textures=[];const u=r.count;for(let f=0;f<u;f++)this.textures[f]=l.clone(),this.textures[f].isRenderTargetTexture=!0,this.textures[f].renderTarget=this;this._setTextureOptions(r),this.depthBuffer=r.depthBuffer,this.stencilBuffer=r.stencilBuffer,this.resolveDepthBuffer=r.resolveDepthBuffer,this.resolveStencilBuffer=r.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=r.depthTexture,this.samples=r.samples,this.multiview=r.multiview}_setTextureOptions(e={}){const t={minFilter:Ei,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let r=0;r<this.textures.length;r++)this.textures[r].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,r=1){if(this.width!==e||this.height!==t||this.depth!==r){this.width=e,this.height=t,this.depth=r;for(let o=0,l=this.textures.length;o<l;o++)this.textures[o].image.width=e,this.textures[o].image.height=t,this.textures[o].image.depth=r,this.textures[o].isArrayTexture=this.textures[o].image.depth>1;this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,r=e.textures.length;t<r;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const o=Object.assign({},e.textures[t].image);this.textures[t].source=new Td(o)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}}class os extends zx{constructor(e=1,t=1,r={}){super(e,t,r),this.isWebGLRenderTarget=!0}}class Y0 extends Nn{constructor(e=null,t=1,r=1,o=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:r,depth:o},this.magFilter=vi,this.minFilter=vi,this.wrapR=is,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class Hx extends Nn{constructor(e=null,t=1,r=1,o=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:r,depth:o},this.magFilter=vi,this.minFilter=vi,this.wrapR=is,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class la{constructor(e=new Q(1/0,1/0,1/0),t=new Q(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,r=e.length;t<r;t+=3)this.expandByPoint(di.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,r=e.count;t<r;t++)this.expandByPoint(di.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,r=e.length;t<r;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const r=di.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(r),this.max.copy(e).add(r),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const r=e.geometry;if(r!==void 0){const l=r.getAttribute("position");if(t===!0&&l!==void 0&&e.isInstancedMesh!==!0)for(let u=0,f=l.count;u<f;u++)e.isMesh===!0?e.getVertexPosition(u,di):di.fromBufferAttribute(l,u),di.applyMatrix4(e.matrixWorld),this.expandByPoint(di);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),ml.copy(e.boundingBox)):(r.boundingBox===null&&r.computeBoundingBox(),ml.copy(r.boundingBox)),ml.applyMatrix4(e.matrixWorld),this.union(ml)}const o=e.children;for(let l=0,u=o.length;l<u;l++)this.expandByObject(o[l],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,di),di.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,r;return e.normal.x>0?(t=e.normal.x*this.min.x,r=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,r=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,r+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,r+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,r+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,r+=e.normal.z*this.min.z),t<=-e.constant&&r>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Vo),gl.subVectors(this.max,Vo),Is.subVectors(e.a,Vo),Us.subVectors(e.b,Vo),Fs.subVectors(e.c,Vo),xr.subVectors(Us,Is),yr.subVectors(Fs,Us),jr.subVectors(Is,Fs);let t=[0,-xr.z,xr.y,0,-yr.z,yr.y,0,-jr.z,jr.y,xr.z,0,-xr.x,yr.z,0,-yr.x,jr.z,0,-jr.x,-xr.y,xr.x,0,-yr.y,yr.x,0,-jr.y,jr.x,0];return!qu(t,Is,Us,Fs,gl)||(t=[1,0,0,0,1,0,0,0,1],!qu(t,Is,Us,Fs,gl))?!1:(vl.crossVectors(xr,yr),t=[vl.x,vl.y,vl.z],qu(t,Is,Us,Fs,gl))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,di).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(di).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(ki[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),ki[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),ki[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),ki[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),ki[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),ki[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),ki[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),ki[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(ki),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const ki=[new Q,new Q,new Q,new Q,new Q,new Q,new Q,new Q],di=new Q,ml=new la,Is=new Q,Us=new Q,Fs=new Q,xr=new Q,yr=new Q,jr=new Q,Vo=new Q,gl=new Q,vl=new Q,qr=new Q;function qu(s,e,t,r,o){for(let l=0,u=s.length-3;l<=u;l+=3){qr.fromArray(s,l);const f=o.x*Math.abs(qr.x)+o.y*Math.abs(qr.y)+o.z*Math.abs(qr.z),d=e.dot(qr),p=t.dot(qr),v=r.dot(qr);if(Math.max(-Math.max(d,p,v),Math.min(d,p,v))>f)return!1}return!0}const Vx=new la,Go=new Q,Yu=new Q;class Ad{constructor(e=new Q,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const r=this.center;t!==void 0?r.copy(t):Vx.setFromPoints(e).getCenter(r);let o=0;for(let l=0,u=e.length;l<u;l++)o=Math.max(o,r.distanceToSquared(e[l]));return this.radius=Math.sqrt(o),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const r=this.center.distanceToSquared(e);return t.copy(e),r>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Go.subVectors(e,this.center);const t=Go.lengthSq();if(t>this.radius*this.radius){const r=Math.sqrt(t),o=(r-this.radius)*.5;this.center.addScaledVector(Go,o/r),this.radius+=o}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Yu.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Go.copy(e.center).add(Yu)),this.expandByPoint(Go.copy(e.center).sub(Yu))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}const Bi=new Q,$u=new Q,_l=new Q,Sr=new Q,Ku=new Q,xl=new Q,Zu=new Q;class $0{constructor(e=new Q,t=new Q(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,Bi)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const r=t.dot(this.direction);return r<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,r)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=Bi.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(Bi.copy(this.origin).addScaledVector(this.direction,t),Bi.distanceToSquared(e))}distanceSqToSegment(e,t,r,o){$u.copy(e).add(t).multiplyScalar(.5),_l.copy(t).sub(e).normalize(),Sr.copy(this.origin).sub($u);const l=e.distanceTo(t)*.5,u=-this.direction.dot(_l),f=Sr.dot(this.direction),d=-Sr.dot(_l),p=Sr.lengthSq(),v=Math.abs(1-u*u);let g,_,S,M;if(v>0)if(g=u*d-f,_=u*f-d,M=l*v,g>=0)if(_>=-M)if(_<=M){const A=1/v;g*=A,_*=A,S=g*(g+u*_+2*f)+_*(u*g+_+2*d)+p}else _=l,g=Math.max(0,-(u*_+f)),S=-g*g+_*(_+2*d)+p;else _=-l,g=Math.max(0,-(u*_+f)),S=-g*g+_*(_+2*d)+p;else _<=-M?(g=Math.max(0,-(-u*l+f)),_=g>0?-l:Math.min(Math.max(-l,-d),l),S=-g*g+_*(_+2*d)+p):_<=M?(g=0,_=Math.min(Math.max(-l,-d),l),S=_*(_+2*d)+p):(g=Math.max(0,-(u*l+f)),_=g>0?l:Math.min(Math.max(-l,-d),l),S=-g*g+_*(_+2*d)+p);else _=u>0?-l:l,g=Math.max(0,-(u*_+f)),S=-g*g+_*(_+2*d)+p;return r&&r.copy(this.origin).addScaledVector(this.direction,g),o&&o.copy($u).addScaledVector(_l,_),S}intersectSphere(e,t){Bi.subVectors(e.center,this.origin);const r=Bi.dot(this.direction),o=Bi.dot(Bi)-r*r,l=e.radius*e.radius;if(o>l)return null;const u=Math.sqrt(l-o),f=r-u,d=r+u;return d<0?null:f<0?this.at(d,t):this.at(f,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const r=-(this.origin.dot(e.normal)+e.constant)/t;return r>=0?r:null}intersectPlane(e,t){const r=this.distanceToPlane(e);return r===null?null:this.at(r,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let r,o,l,u,f,d;const p=1/this.direction.x,v=1/this.direction.y,g=1/this.direction.z,_=this.origin;return p>=0?(r=(e.min.x-_.x)*p,o=(e.max.x-_.x)*p):(r=(e.max.x-_.x)*p,o=(e.min.x-_.x)*p),v>=0?(l=(e.min.y-_.y)*v,u=(e.max.y-_.y)*v):(l=(e.max.y-_.y)*v,u=(e.min.y-_.y)*v),r>u||l>o||((l>r||isNaN(r))&&(r=l),(u<o||isNaN(o))&&(o=u),g>=0?(f=(e.min.z-_.z)*g,d=(e.max.z-_.z)*g):(f=(e.max.z-_.z)*g,d=(e.min.z-_.z)*g),r>d||f>o)||((f>r||r!==r)&&(r=f),(d<o||o!==o)&&(o=d),o<0)?null:this.at(r>=0?r:o,t)}intersectsBox(e){return this.intersectBox(e,Bi)!==null}intersectTriangle(e,t,r,o,l){Ku.subVectors(t,e),xl.subVectors(r,e),Zu.crossVectors(Ku,xl);let u=this.direction.dot(Zu),f;if(u>0){if(o)return null;f=1}else if(u<0)f=-1,u=-u;else return null;Sr.subVectors(this.origin,e);const d=f*this.direction.dot(xl.crossVectors(Sr,xl));if(d<0)return null;const p=f*this.direction.dot(Ku.cross(Sr));if(p<0||d+p>u)return null;const v=-f*Sr.dot(Zu);return v<0?null:this.at(v/u,l)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class $t{constructor(e,t,r,o,l,u,f,d,p,v,g,_,S,M,A,y){$t.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,r,o,l,u,f,d,p,v,g,_,S,M,A,y)}set(e,t,r,o,l,u,f,d,p,v,g,_,S,M,A,y){const x=this.elements;return x[0]=e,x[4]=t,x[8]=r,x[12]=o,x[1]=l,x[5]=u,x[9]=f,x[13]=d,x[2]=p,x[6]=v,x[10]=g,x[14]=_,x[3]=S,x[7]=M,x[11]=A,x[15]=y,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new $t().fromArray(this.elements)}copy(e){const t=this.elements,r=e.elements;return t[0]=r[0],t[1]=r[1],t[2]=r[2],t[3]=r[3],t[4]=r[4],t[5]=r[5],t[6]=r[6],t[7]=r[7],t[8]=r[8],t[9]=r[9],t[10]=r[10],t[11]=r[11],t[12]=r[12],t[13]=r[13],t[14]=r[14],t[15]=r[15],this}copyPosition(e){const t=this.elements,r=e.elements;return t[12]=r[12],t[13]=r[13],t[14]=r[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,r){return e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),r.setFromMatrixColumn(this,2),this}makeBasis(e,t,r){return this.set(e.x,t.x,r.x,0,e.y,t.y,r.y,0,e.z,t.z,r.z,0,0,0,0,1),this}extractRotation(e){const t=this.elements,r=e.elements,o=1/Os.setFromMatrixColumn(e,0).length(),l=1/Os.setFromMatrixColumn(e,1).length(),u=1/Os.setFromMatrixColumn(e,2).length();return t[0]=r[0]*o,t[1]=r[1]*o,t[2]=r[2]*o,t[3]=0,t[4]=r[4]*l,t[5]=r[5]*l,t[6]=r[6]*l,t[7]=0,t[8]=r[8]*u,t[9]=r[9]*u,t[10]=r[10]*u,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,r=e.x,o=e.y,l=e.z,u=Math.cos(r),f=Math.sin(r),d=Math.cos(o),p=Math.sin(o),v=Math.cos(l),g=Math.sin(l);if(e.order==="XYZ"){const _=u*v,S=u*g,M=f*v,A=f*g;t[0]=d*v,t[4]=-d*g,t[8]=p,t[1]=S+M*p,t[5]=_-A*p,t[9]=-f*d,t[2]=A-_*p,t[6]=M+S*p,t[10]=u*d}else if(e.order==="YXZ"){const _=d*v,S=d*g,M=p*v,A=p*g;t[0]=_+A*f,t[4]=M*f-S,t[8]=u*p,t[1]=u*g,t[5]=u*v,t[9]=-f,t[2]=S*f-M,t[6]=A+_*f,t[10]=u*d}else if(e.order==="ZXY"){const _=d*v,S=d*g,M=p*v,A=p*g;t[0]=_-A*f,t[4]=-u*g,t[8]=M+S*f,t[1]=S+M*f,t[5]=u*v,t[9]=A-_*f,t[2]=-u*p,t[6]=f,t[10]=u*d}else if(e.order==="ZYX"){const _=u*v,S=u*g,M=f*v,A=f*g;t[0]=d*v,t[4]=M*p-S,t[8]=_*p+A,t[1]=d*g,t[5]=A*p+_,t[9]=S*p-M,t[2]=-p,t[6]=f*d,t[10]=u*d}else if(e.order==="YZX"){const _=u*d,S=u*p,M=f*d,A=f*p;t[0]=d*v,t[4]=A-_*g,t[8]=M*g+S,t[1]=g,t[5]=u*v,t[9]=-f*v,t[2]=-p*v,t[6]=S*g+M,t[10]=_-A*g}else if(e.order==="XZY"){const _=u*d,S=u*p,M=f*d,A=f*p;t[0]=d*v,t[4]=-g,t[8]=p*v,t[1]=_*g+A,t[5]=u*v,t[9]=S*g-M,t[2]=M*g-S,t[6]=f*v,t[10]=A*g+_}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Gx,e,Wx)}lookAt(e,t,r){const o=this.elements;return $n.subVectors(e,t),$n.lengthSq()===0&&($n.z=1),$n.normalize(),Mr.crossVectors(r,$n),Mr.lengthSq()===0&&(Math.abs(r.z)===1?$n.x+=1e-4:$n.z+=1e-4,$n.normalize(),Mr.crossVectors(r,$n)),Mr.normalize(),yl.crossVectors($n,Mr),o[0]=Mr.x,o[4]=yl.x,o[8]=$n.x,o[1]=Mr.y,o[5]=yl.y,o[9]=$n.y,o[2]=Mr.z,o[6]=yl.z,o[10]=$n.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const r=e.elements,o=t.elements,l=this.elements,u=r[0],f=r[4],d=r[8],p=r[12],v=r[1],g=r[5],_=r[9],S=r[13],M=r[2],A=r[6],y=r[10],x=r[14],O=r[3],D=r[7],R=r[11],z=r[15],H=o[0],I=o[4],N=o[8],C=o[12],T=o[1],F=o[5],$=o[9],ee=o[13],le=o[2],ne=o[6],ce=o[10],re=o[14],V=o[3],me=o[7],ie=o[11],P=o[15];return l[0]=u*H+f*T+d*le+p*V,l[4]=u*I+f*F+d*ne+p*me,l[8]=u*N+f*$+d*ce+p*ie,l[12]=u*C+f*ee+d*re+p*P,l[1]=v*H+g*T+_*le+S*V,l[5]=v*I+g*F+_*ne+S*me,l[9]=v*N+g*$+_*ce+S*ie,l[13]=v*C+g*ee+_*re+S*P,l[2]=M*H+A*T+y*le+x*V,l[6]=M*I+A*F+y*ne+x*me,l[10]=M*N+A*$+y*ce+x*ie,l[14]=M*C+A*ee+y*re+x*P,l[3]=O*H+D*T+R*le+z*V,l[7]=O*I+D*F+R*ne+z*me,l[11]=O*N+D*$+R*ce+z*ie,l[15]=O*C+D*ee+R*re+z*P,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],r=e[4],o=e[8],l=e[12],u=e[1],f=e[5],d=e[9],p=e[13],v=e[2],g=e[6],_=e[10],S=e[14],M=e[3],A=e[7],y=e[11],x=e[15];return M*(+l*d*g-o*p*g-l*f*_+r*p*_+o*f*S-r*d*S)+A*(+t*d*S-t*p*_+l*u*_-o*u*S+o*p*v-l*d*v)+y*(+t*p*g-t*f*S-l*u*g+r*u*S+l*f*v-r*p*v)+x*(-o*f*v-t*d*g+t*f*_+o*u*g-r*u*_+r*d*v)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,r){const o=this.elements;return e.isVector3?(o[12]=e.x,o[13]=e.y,o[14]=e.z):(o[12]=e,o[13]=t,o[14]=r),this}invert(){const e=this.elements,t=e[0],r=e[1],o=e[2],l=e[3],u=e[4],f=e[5],d=e[6],p=e[7],v=e[8],g=e[9],_=e[10],S=e[11],M=e[12],A=e[13],y=e[14],x=e[15],O=g*y*p-A*_*p+A*d*S-f*y*S-g*d*x+f*_*x,D=M*_*p-v*y*p-M*d*S+u*y*S+v*d*x-u*_*x,R=v*A*p-M*g*p+M*f*S-u*A*S-v*f*x+u*g*x,z=M*g*d-v*A*d-M*f*_+u*A*_+v*f*y-u*g*y,H=t*O+r*D+o*R+l*z;if(H===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const I=1/H;return e[0]=O*I,e[1]=(A*_*l-g*y*l-A*o*S+r*y*S+g*o*x-r*_*x)*I,e[2]=(f*y*l-A*d*l+A*o*p-r*y*p-f*o*x+r*d*x)*I,e[3]=(g*d*l-f*_*l-g*o*p+r*_*p+f*o*S-r*d*S)*I,e[4]=D*I,e[5]=(v*y*l-M*_*l+M*o*S-t*y*S-v*o*x+t*_*x)*I,e[6]=(M*d*l-u*y*l-M*o*p+t*y*p+u*o*x-t*d*x)*I,e[7]=(u*_*l-v*d*l+v*o*p-t*_*p-u*o*S+t*d*S)*I,e[8]=R*I,e[9]=(M*g*l-v*A*l-M*r*S+t*A*S+v*r*x-t*g*x)*I,e[10]=(u*A*l-M*f*l+M*r*p-t*A*p-u*r*x+t*f*x)*I,e[11]=(v*f*l-u*g*l-v*r*p+t*g*p+u*r*S-t*f*S)*I,e[12]=z*I,e[13]=(v*A*o-M*g*o+M*r*_-t*A*_-v*r*y+t*g*y)*I,e[14]=(M*f*o-u*A*o-M*r*d+t*A*d+u*r*y-t*f*y)*I,e[15]=(u*g*o-v*f*o+v*r*d-t*g*d-u*r*_+t*f*_)*I,this}scale(e){const t=this.elements,r=e.x,o=e.y,l=e.z;return t[0]*=r,t[4]*=o,t[8]*=l,t[1]*=r,t[5]*=o,t[9]*=l,t[2]*=r,t[6]*=o,t[10]*=l,t[3]*=r,t[7]*=o,t[11]*=l,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],r=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],o=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,r,o))}makeTranslation(e,t,r){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,r,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),r=Math.sin(e);return this.set(1,0,0,0,0,t,-r,0,0,r,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,0,r,0,0,1,0,0,-r,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,-r,0,0,r,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const r=Math.cos(t),o=Math.sin(t),l=1-r,u=e.x,f=e.y,d=e.z,p=l*u,v=l*f;return this.set(p*u+r,p*f-o*d,p*d+o*f,0,p*f+o*d,v*f+r,v*d-o*u,0,p*d-o*f,v*d+o*u,l*d*d+r,0,0,0,0,1),this}makeScale(e,t,r){return this.set(e,0,0,0,0,t,0,0,0,0,r,0,0,0,0,1),this}makeShear(e,t,r,o,l,u){return this.set(1,r,l,0,e,1,u,0,t,o,1,0,0,0,0,1),this}compose(e,t,r){const o=this.elements,l=t._x,u=t._y,f=t._z,d=t._w,p=l+l,v=u+u,g=f+f,_=l*p,S=l*v,M=l*g,A=u*v,y=u*g,x=f*g,O=d*p,D=d*v,R=d*g,z=r.x,H=r.y,I=r.z;return o[0]=(1-(A+x))*z,o[1]=(S+R)*z,o[2]=(M-D)*z,o[3]=0,o[4]=(S-R)*H,o[5]=(1-(_+x))*H,o[6]=(y+O)*H,o[7]=0,o[8]=(M+D)*I,o[9]=(y-O)*I,o[10]=(1-(_+A))*I,o[11]=0,o[12]=e.x,o[13]=e.y,o[14]=e.z,o[15]=1,this}decompose(e,t,r){const o=this.elements;let l=Os.set(o[0],o[1],o[2]).length();const u=Os.set(o[4],o[5],o[6]).length(),f=Os.set(o[8],o[9],o[10]).length();this.determinant()<0&&(l=-l),e.x=o[12],e.y=o[13],e.z=o[14],hi.copy(this);const p=1/l,v=1/u,g=1/f;return hi.elements[0]*=p,hi.elements[1]*=p,hi.elements[2]*=p,hi.elements[4]*=v,hi.elements[5]*=v,hi.elements[6]*=v,hi.elements[8]*=g,hi.elements[9]*=g,hi.elements[10]*=g,t.setFromRotationMatrix(hi),r.x=l,r.y=u,r.z=f,this}makePerspective(e,t,r,o,l,u,f=wi,d=!1){const p=this.elements,v=2*l/(t-e),g=2*l/(r-o),_=(t+e)/(t-e),S=(r+o)/(r-o);let M,A;if(d)M=l/(u-l),A=u*l/(u-l);else if(f===wi)M=-(u+l)/(u-l),A=-2*u*l/(u-l);else if(f===Kl)M=-u/(u-l),A=-u*l/(u-l);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+f);return p[0]=v,p[4]=0,p[8]=_,p[12]=0,p[1]=0,p[5]=g,p[9]=S,p[13]=0,p[2]=0,p[6]=0,p[10]=M,p[14]=A,p[3]=0,p[7]=0,p[11]=-1,p[15]=0,this}makeOrthographic(e,t,r,o,l,u,f=wi,d=!1){const p=this.elements,v=2/(t-e),g=2/(r-o),_=-(t+e)/(t-e),S=-(r+o)/(r-o);let M,A;if(d)M=1/(u-l),A=u/(u-l);else if(f===wi)M=-2/(u-l),A=-(u+l)/(u-l);else if(f===Kl)M=-1/(u-l),A=-l/(u-l);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+f);return p[0]=v,p[4]=0,p[8]=0,p[12]=_,p[1]=0,p[5]=g,p[9]=0,p[13]=S,p[2]=0,p[6]=0,p[10]=M,p[14]=A,p[3]=0,p[7]=0,p[11]=0,p[15]=1,this}equals(e){const t=this.elements,r=e.elements;for(let o=0;o<16;o++)if(t[o]!==r[o])return!1;return!0}fromArray(e,t=0){for(let r=0;r<16;r++)this.elements[r]=e[r+t];return this}toArray(e=[],t=0){const r=this.elements;return e[t]=r[0],e[t+1]=r[1],e[t+2]=r[2],e[t+3]=r[3],e[t+4]=r[4],e[t+5]=r[5],e[t+6]=r[6],e[t+7]=r[7],e[t+8]=r[8],e[t+9]=r[9],e[t+10]=r[10],e[t+11]=r[11],e[t+12]=r[12],e[t+13]=r[13],e[t+14]=r[14],e[t+15]=r[15],e}}const Os=new Q,hi=new $t,Gx=new Q(0,0,0),Wx=new Q(1,1,1),Mr=new Q,yl=new Q,$n=new Q,Cm=new $t,bm=new aa;class Ri{constructor(e=0,t=0,r=0,o=Ri.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=r,this._order=o}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,r,o=this._order){return this._x=e,this._y=t,this._z=r,this._order=o,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,r=!0){const o=e.elements,l=o[0],u=o[4],f=o[8],d=o[1],p=o[5],v=o[9],g=o[2],_=o[6],S=o[10];switch(t){case"XYZ":this._y=Math.asin(Ct(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(-v,S),this._z=Math.atan2(-u,l)):(this._x=Math.atan2(_,p),this._z=0);break;case"YXZ":this._x=Math.asin(-Ct(v,-1,1)),Math.abs(v)<.9999999?(this._y=Math.atan2(f,S),this._z=Math.atan2(d,p)):(this._y=Math.atan2(-g,l),this._z=0);break;case"ZXY":this._x=Math.asin(Ct(_,-1,1)),Math.abs(_)<.9999999?(this._y=Math.atan2(-g,S),this._z=Math.atan2(-u,p)):(this._y=0,this._z=Math.atan2(d,l));break;case"ZYX":this._y=Math.asin(-Ct(g,-1,1)),Math.abs(g)<.9999999?(this._x=Math.atan2(_,S),this._z=Math.atan2(d,l)):(this._x=0,this._z=Math.atan2(-u,p));break;case"YZX":this._z=Math.asin(Ct(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(-v,p),this._y=Math.atan2(-g,l)):(this._x=0,this._y=Math.atan2(f,S));break;case"XZY":this._z=Math.asin(-Ct(u,-1,1)),Math.abs(u)<.9999999?(this._x=Math.atan2(_,p),this._y=Math.atan2(f,l)):(this._x=Math.atan2(-v,S),this._y=0);break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,r===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,r){return Cm.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Cm,t,r)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return bm.setFromEuler(this),this.setFromQuaternion(bm,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Ri.DEFAULT_ORDER="XYZ";class Rd{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let Xx=0;const Pm=new Q,ks=new aa,zi=new $t,Sl=new Q,Wo=new Q,jx=new Q,qx=new aa,Lm=new Q(1,0,0),Dm=new Q(0,1,0),Nm=new Q(0,0,1),Im={type:"added"},Yx={type:"removed"},Bs={type:"childadded",child:null},Ju={type:"childremoved",child:null};class _n extends so{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Xx++}),this.uuid=oo(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=_n.DEFAULT_UP.clone();const e=new Q,t=new Ri,r=new aa,o=new Q(1,1,1);function l(){r.setFromEuler(t,!1)}function u(){t.setFromQuaternion(r,void 0,!1)}t._onChange(l),r._onChange(u),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:r},scale:{configurable:!0,enumerable:!0,value:o},modelViewMatrix:{value:new $t},normalMatrix:{value:new Et}}),this.matrix=new $t,this.matrixWorld=new $t,this.matrixAutoUpdate=_n.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Rd,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return ks.setFromAxisAngle(e,t),this.quaternion.multiply(ks),this}rotateOnWorldAxis(e,t){return ks.setFromAxisAngle(e,t),this.quaternion.premultiply(ks),this}rotateX(e){return this.rotateOnAxis(Lm,e)}rotateY(e){return this.rotateOnAxis(Dm,e)}rotateZ(e){return this.rotateOnAxis(Nm,e)}translateOnAxis(e,t){return Pm.copy(e).applyQuaternion(this.quaternion),this.position.add(Pm.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Lm,e)}translateY(e){return this.translateOnAxis(Dm,e)}translateZ(e){return this.translateOnAxis(Nm,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(zi.copy(this.matrixWorld).invert())}lookAt(e,t,r){e.isVector3?Sl.copy(e):Sl.set(e,t,r);const o=this.parent;this.updateWorldMatrix(!0,!1),Wo.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?zi.lookAt(Wo,Sl,this.up):zi.lookAt(Sl,Wo,this.up),this.quaternion.setFromRotationMatrix(zi),o&&(zi.extractRotation(o.matrixWorld),ks.setFromRotationMatrix(zi),this.quaternion.premultiply(ks.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(console.error("THREE.Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Im),Bs.child=e,this.dispatchEvent(Bs),Bs.child=null):console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let r=0;r<arguments.length;r++)this.remove(arguments[r]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Yx),Ju.child=e,this.dispatchEvent(Ju),Ju.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),zi.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),zi.multiply(e.parent.matrixWorld)),e.applyMatrix4(zi),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Im),Bs.child=e,this.dispatchEvent(Bs),Bs.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let r=0,o=this.children.length;r<o;r++){const u=this.children[r].getObjectByProperty(e,t);if(u!==void 0)return u}}getObjectsByProperty(e,t,r=[]){this[e]===t&&r.push(this);const o=this.children;for(let l=0,u=o.length;l<u;l++)o[l].getObjectsByProperty(e,t,r);return r}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Wo,e,jx),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Wo,qx,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let r=0,o=t.length;r<o;r++)t[r].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let r=0,o=t.length;r<o;r++)t[r].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let r=0,o=t.length;r<o;r++)t[r].updateMatrixWorld(e)}updateWorldMatrix(e,t){const r=this.parent;if(e===!0&&r!==null&&r.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){const o=this.children;for(let l=0,u=o.length;l<u;l++)o[l].updateWorldMatrix(!1,!0)}}toJSON(e){const t=e===void 0||typeof e=="string",r={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},r.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const o={};o.uuid=this.uuid,o.type=this.type,this.name!==""&&(o.name=this.name),this.castShadow===!0&&(o.castShadow=!0),this.receiveShadow===!0&&(o.receiveShadow=!0),this.visible===!1&&(o.visible=!1),this.frustumCulled===!1&&(o.frustumCulled=!1),this.renderOrder!==0&&(o.renderOrder=this.renderOrder),Object.keys(this.userData).length>0&&(o.userData=this.userData),o.layers=this.layers.mask,o.matrix=this.matrix.toArray(),o.up=this.up.toArray(),this.matrixAutoUpdate===!1&&(o.matrixAutoUpdate=!1),this.isInstancedMesh&&(o.type="InstancedMesh",o.count=this.count,o.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(o.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(o.type="BatchedMesh",o.perObjectFrustumCulled=this.perObjectFrustumCulled,o.sortObjects=this.sortObjects,o.drawRanges=this._drawRanges,o.reservedRanges=this._reservedRanges,o.geometryInfo=this._geometryInfo.map(f=>({...f,boundingBox:f.boundingBox?f.boundingBox.toJSON():void 0,boundingSphere:f.boundingSphere?f.boundingSphere.toJSON():void 0})),o.instanceInfo=this._instanceInfo.map(f=>({...f})),o.availableInstanceIds=this._availableInstanceIds.slice(),o.availableGeometryIds=this._availableGeometryIds.slice(),o.nextIndexStart=this._nextIndexStart,o.nextVertexStart=this._nextVertexStart,o.geometryCount=this._geometryCount,o.maxInstanceCount=this._maxInstanceCount,o.maxVertexCount=this._maxVertexCount,o.maxIndexCount=this._maxIndexCount,o.geometryInitialized=this._geometryInitialized,o.matricesTexture=this._matricesTexture.toJSON(e),o.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(o.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(o.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(o.boundingBox=this.boundingBox.toJSON()));function l(f,d){return f[d.uuid]===void 0&&(f[d.uuid]=d.toJSON(e)),d.uuid}if(this.isScene)this.background&&(this.background.isColor?o.background=this.background.toJSON():this.background.isTexture&&(o.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(o.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){o.geometry=l(e.geometries,this.geometry);const f=this.geometry.parameters;if(f!==void 0&&f.shapes!==void 0){const d=f.shapes;if(Array.isArray(d))for(let p=0,v=d.length;p<v;p++){const g=d[p];l(e.shapes,g)}else l(e.shapes,d)}}if(this.isSkinnedMesh&&(o.bindMode=this.bindMode,o.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(l(e.skeletons,this.skeleton),o.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const f=[];for(let d=0,p=this.material.length;d<p;d++)f.push(l(e.materials,this.material[d]));o.material=f}else o.material=l(e.materials,this.material);if(this.children.length>0){o.children=[];for(let f=0;f<this.children.length;f++)o.children.push(this.children[f].toJSON(e).object)}if(this.animations.length>0){o.animations=[];for(let f=0;f<this.animations.length;f++){const d=this.animations[f];o.animations.push(l(e.animations,d))}}if(t){const f=u(e.geometries),d=u(e.materials),p=u(e.textures),v=u(e.images),g=u(e.shapes),_=u(e.skeletons),S=u(e.animations),M=u(e.nodes);f.length>0&&(r.geometries=f),d.length>0&&(r.materials=d),p.length>0&&(r.textures=p),v.length>0&&(r.images=v),g.length>0&&(r.shapes=g),_.length>0&&(r.skeletons=_),S.length>0&&(r.animations=S),M.length>0&&(r.nodes=M)}return r.object=o,r;function u(f){const d=[];for(const p in f){const v=f[p];delete v.metadata,d.push(v)}return d}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let r=0;r<e.children.length;r++){const o=e.children[r];this.add(o.clone())}return this}}_n.DEFAULT_UP=new Q(0,1,0);_n.DEFAULT_MATRIX_AUTO_UPDATE=!0;_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;const pi=new Q,Hi=new Q,Qu=new Q,Vi=new Q,zs=new Q,Hs=new Q,Um=new Q,ef=new Q,tf=new Q,nf=new Q,rf=new Zt,sf=new Zt,of=new Zt;class mi{constructor(e=new Q,t=new Q,r=new Q){this.a=e,this.b=t,this.c=r}static getNormal(e,t,r,o){o.subVectors(r,t),pi.subVectors(e,t),o.cross(pi);const l=o.lengthSq();return l>0?o.multiplyScalar(1/Math.sqrt(l)):o.set(0,0,0)}static getBarycoord(e,t,r,o,l){pi.subVectors(o,t),Hi.subVectors(r,t),Qu.subVectors(e,t);const u=pi.dot(pi),f=pi.dot(Hi),d=pi.dot(Qu),p=Hi.dot(Hi),v=Hi.dot(Qu),g=u*p-f*f;if(g===0)return l.set(0,0,0),null;const _=1/g,S=(p*d-f*v)*_,M=(u*v-f*d)*_;return l.set(1-S-M,M,S)}static containsPoint(e,t,r,o){return this.getBarycoord(e,t,r,o,Vi)===null?!1:Vi.x>=0&&Vi.y>=0&&Vi.x+Vi.y<=1}static getInterpolation(e,t,r,o,l,u,f,d){return this.getBarycoord(e,t,r,o,Vi)===null?(d.x=0,d.y=0,"z"in d&&(d.z=0),"w"in d&&(d.w=0),null):(d.setScalar(0),d.addScaledVector(l,Vi.x),d.addScaledVector(u,Vi.y),d.addScaledVector(f,Vi.z),d)}static getInterpolatedAttribute(e,t,r,o,l,u){return rf.setScalar(0),sf.setScalar(0),of.setScalar(0),rf.fromBufferAttribute(e,t),sf.fromBufferAttribute(e,r),of.fromBufferAttribute(e,o),u.setScalar(0),u.addScaledVector(rf,l.x),u.addScaledVector(sf,l.y),u.addScaledVector(of,l.z),u}static isFrontFacing(e,t,r,o){return pi.subVectors(r,t),Hi.subVectors(e,t),pi.cross(Hi).dot(o)<0}set(e,t,r){return this.a.copy(e),this.b.copy(t),this.c.copy(r),this}setFromPointsAndIndices(e,t,r,o){return this.a.copy(e[t]),this.b.copy(e[r]),this.c.copy(e[o]),this}setFromAttributeAndIndices(e,t,r,o){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,r),this.c.fromBufferAttribute(e,o),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return pi.subVectors(this.c,this.b),Hi.subVectors(this.a,this.b),pi.cross(Hi).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return mi.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return mi.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,r,o,l){return mi.getInterpolation(e,this.a,this.b,this.c,t,r,o,l)}containsPoint(e){return mi.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return mi.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const r=this.a,o=this.b,l=this.c;let u,f;zs.subVectors(o,r),Hs.subVectors(l,r),ef.subVectors(e,r);const d=zs.dot(ef),p=Hs.dot(ef);if(d<=0&&p<=0)return t.copy(r);tf.subVectors(e,o);const v=zs.dot(tf),g=Hs.dot(tf);if(v>=0&&g<=v)return t.copy(o);const _=d*g-v*p;if(_<=0&&d>=0&&v<=0)return u=d/(d-v),t.copy(r).addScaledVector(zs,u);nf.subVectors(e,l);const S=zs.dot(nf),M=Hs.dot(nf);if(M>=0&&S<=M)return t.copy(l);const A=S*p-d*M;if(A<=0&&p>=0&&M<=0)return f=p/(p-M),t.copy(r).addScaledVector(Hs,f);const y=v*M-S*g;if(y<=0&&g-v>=0&&S-M>=0)return Um.subVectors(l,o),f=(g-v)/(g-v+(S-M)),t.copy(o).addScaledVector(Um,f);const x=1/(y+A+_);return u=A*x,f=_*x,t.copy(r).addScaledVector(zs,u).addScaledVector(Hs,f)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}const K0={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Er={h:0,s:0,l:0},Ml={h:0,s:0,l:0};function af(s,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?s+(e-s)*6*t:t<1/2?e:t<2/3?s+(e-s)*6*(2/3-t):s}class It{constructor(e,t,r){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,r)}set(e,t,r){if(t===void 0&&r===void 0){const o=e;o&&o.isColor?this.copy(o):typeof o=="number"?this.setHex(o):typeof o=="string"&&this.setStyle(o)}else this.setRGB(e,t,r);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Vn){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,Nt.colorSpaceToWorking(this,t),this}setRGB(e,t,r,o=Nt.workingColorSpace){return this.r=e,this.g=t,this.b=r,Nt.colorSpaceToWorking(this,o),this}setHSL(e,t,r,o=Nt.workingColorSpace){if(e=Nx(e,1),t=Ct(t,0,1),r=Ct(r,0,1),t===0)this.r=this.g=this.b=r;else{const l=r<=.5?r*(1+t):r+t-r*t,u=2*r-l;this.r=af(u,l,e+1/3),this.g=af(u,l,e),this.b=af(u,l,e-1/3)}return Nt.colorSpaceToWorking(this,o),this}setStyle(e,t=Vn){function r(l){l!==void 0&&parseFloat(l)<1&&console.warn("THREE.Color: Alpha component of "+e+" will be ignored.")}let o;if(o=/^(\w+)\(([^\)]*)\)/.exec(e)){let l;const u=o[1],f=o[2];switch(u){case"rgb":case"rgba":if(l=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(f))return r(l[4]),this.setRGB(Math.min(255,parseInt(l[1],10))/255,Math.min(255,parseInt(l[2],10))/255,Math.min(255,parseInt(l[3],10))/255,t);if(l=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(f))return r(l[4]),this.setRGB(Math.min(100,parseInt(l[1],10))/100,Math.min(100,parseInt(l[2],10))/100,Math.min(100,parseInt(l[3],10))/100,t);break;case"hsl":case"hsla":if(l=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(f))return r(l[4]),this.setHSL(parseFloat(l[1])/360,parseFloat(l[2])/100,parseFloat(l[3])/100,t);break;default:console.warn("THREE.Color: Unknown color model "+e)}}else if(o=/^\#([A-Fa-f\d]+)$/.exec(e)){const l=o[1],u=l.length;if(u===3)return this.setRGB(parseInt(l.charAt(0),16)/15,parseInt(l.charAt(1),16)/15,parseInt(l.charAt(2),16)/15,t);if(u===6)return this.setHex(parseInt(l,16),t);console.warn("THREE.Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Vn){const r=K0[e.toLowerCase()];return r!==void 0?this.setHex(r,t):console.warn("THREE.Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Yi(e.r),this.g=Yi(e.g),this.b=Yi(e.b),this}copyLinearToSRGB(e){return this.r=Zs(e.r),this.g=Zs(e.g),this.b=Zs(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Vn){return Nt.workingToColorSpace(Rn.copy(this),e),Math.round(Ct(Rn.r*255,0,255))*65536+Math.round(Ct(Rn.g*255,0,255))*256+Math.round(Ct(Rn.b*255,0,255))}getHexString(e=Vn){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=Nt.workingColorSpace){Nt.workingToColorSpace(Rn.copy(this),t);const r=Rn.r,o=Rn.g,l=Rn.b,u=Math.max(r,o,l),f=Math.min(r,o,l);let d,p;const v=(f+u)/2;if(f===u)d=0,p=0;else{const g=u-f;switch(p=v<=.5?g/(u+f):g/(2-u-f),u){case r:d=(o-l)/g+(o<l?6:0);break;case o:d=(l-r)/g+2;break;case l:d=(r-o)/g+4;break}d/=6}return e.h=d,e.s=p,e.l=v,e}getRGB(e,t=Nt.workingColorSpace){return Nt.workingToColorSpace(Rn.copy(this),t),e.r=Rn.r,e.g=Rn.g,e.b=Rn.b,e}getStyle(e=Vn){Nt.workingToColorSpace(Rn.copy(this),e);const t=Rn.r,r=Rn.g,o=Rn.b;return e!==Vn?`color(${e} ${t.toFixed(3)} ${r.toFixed(3)} ${o.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(r*255)},${Math.round(o*255)})`}offsetHSL(e,t,r){return this.getHSL(Er),this.setHSL(Er.h+e,Er.s+t,Er.l+r)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,r){return this.r=e.r+(t.r-e.r)*r,this.g=e.g+(t.g-e.g)*r,this.b=e.b+(t.b-e.b)*r,this}lerpHSL(e,t){this.getHSL(Er),e.getHSL(Ml);const r=Vu(Er.h,Ml.h,t),o=Vu(Er.s,Ml.s,t),l=Vu(Er.l,Ml.l,t);return this.setHSL(r,o,l),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,r=this.g,o=this.b,l=e.elements;return this.r=l[0]*t+l[3]*r+l[6]*o,this.g=l[1]*t+l[4]*r+l[7]*o,this.b=l[2]*t+l[5]*r+l[8]*o,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const Rn=new It;It.NAMES=K0;let $x=0;class ca extends so{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:$x++}),this.uuid=oo(),this.name="",this.type="Material",this.blending=Ks,this.side=Cr,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Mf,this.blendDst=Ef,this.blendEquation=ts,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new It(0,0,0),this.blendAlpha=0,this.depthFunc=Js,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Sm,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Ds,this.stencilZFail=Ds,this.stencilZPass=Ds,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const r=e[t];if(r===void 0){console.warn(`THREE.Material: parameter '${t}' has value of undefined.`);continue}const o=this[t];if(o===void 0){console.warn(`THREE.Material: '${t}' is not a property of THREE.${this.type}.`);continue}o&&o.isColor?o.set(r):o&&o.isVector3&&r&&r.isVector3?o.copy(r):this[t]=r}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const r={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.color&&this.color.isColor&&(r.color=this.color.getHex()),this.roughness!==void 0&&(r.roughness=this.roughness),this.metalness!==void 0&&(r.metalness=this.metalness),this.sheen!==void 0&&(r.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(r.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(r.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(r.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(r.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(r.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(r.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(r.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(r.shininess=this.shininess),this.clearcoat!==void 0&&(r.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(r.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(r.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(r.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(r.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,r.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(r.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(r.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(r.dispersion=this.dispersion),this.iridescence!==void 0&&(r.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(r.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(r.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(r.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(r.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(r.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(r.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(r.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(r.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(r.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(r.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(r.lightMap=this.lightMap.toJSON(e).uuid,r.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(r.aoMap=this.aoMap.toJSON(e).uuid,r.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(r.bumpMap=this.bumpMap.toJSON(e).uuid,r.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(r.normalMap=this.normalMap.toJSON(e).uuid,r.normalMapType=this.normalMapType,r.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(r.displacementMap=this.displacementMap.toJSON(e).uuid,r.displacementScale=this.displacementScale,r.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(r.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(r.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(r.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(r.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(r.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(r.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(r.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(r.combine=this.combine)),this.envMapRotation!==void 0&&(r.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(r.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(r.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(r.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(r.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(r.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(r.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(r.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(r.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(r.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(r.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(r.size=this.size),this.shadowSide!==null&&(r.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(r.sizeAttenuation=this.sizeAttenuation),this.blending!==Ks&&(r.blending=this.blending),this.side!==Cr&&(r.side=this.side),this.vertexColors===!0&&(r.vertexColors=!0),this.opacity<1&&(r.opacity=this.opacity),this.transparent===!0&&(r.transparent=!0),this.blendSrc!==Mf&&(r.blendSrc=this.blendSrc),this.blendDst!==Ef&&(r.blendDst=this.blendDst),this.blendEquation!==ts&&(r.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(r.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(r.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(r.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(r.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(r.blendAlpha=this.blendAlpha),this.depthFunc!==Js&&(r.depthFunc=this.depthFunc),this.depthTest===!1&&(r.depthTest=this.depthTest),this.depthWrite===!1&&(r.depthWrite=this.depthWrite),this.colorWrite===!1&&(r.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(r.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==Sm&&(r.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(r.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(r.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Ds&&(r.stencilFail=this.stencilFail),this.stencilZFail!==Ds&&(r.stencilZFail=this.stencilZFail),this.stencilZPass!==Ds&&(r.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(r.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(r.rotation=this.rotation),this.polygonOffset===!0&&(r.polygonOffset=!0),this.polygonOffsetFactor!==0&&(r.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(r.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(r.linewidth=this.linewidth),this.dashSize!==void 0&&(r.dashSize=this.dashSize),this.gapSize!==void 0&&(r.gapSize=this.gapSize),this.scale!==void 0&&(r.scale=this.scale),this.dithering===!0&&(r.dithering=!0),this.alphaTest>0&&(r.alphaTest=this.alphaTest),this.alphaHash===!0&&(r.alphaHash=!0),this.alphaToCoverage===!0&&(r.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(r.premultipliedAlpha=!0),this.forceSinglePass===!0&&(r.forceSinglePass=!0),this.wireframe===!0&&(r.wireframe=!0),this.wireframeLinewidth>1&&(r.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(r.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(r.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(r.flatShading=!0),this.visible===!1&&(r.visible=!1),this.toneMapped===!1&&(r.toneMapped=!1),this.fog===!1&&(r.fog=!1),Object.keys(this.userData).length>0&&(r.userData=this.userData);function o(l){const u=[];for(const f in l){const d=l[f];delete d.metadata,u.push(d)}return u}if(t){const l=o(e.textures),u=o(e.images);l.length>0&&(r.textures=l),u.length>0&&(r.images=u)}return r}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let r=null;if(t!==null){const o=t.length;r=new Array(o);for(let l=0;l!==o;++l)r[l]=t[l].clone()}return this.clippingPlanes=r,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}class Jl extends ca{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new It(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Ri,this.combine=U0,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const nn=new Q,El=new Ge;let Kx=0;class Ti{constructor(e,t,r=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Kx++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=r,this.usage=Mm,this.updateRanges=[],this.gpuType=Xi,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,r){e*=this.itemSize,r*=t.itemSize;for(let o=0,l=this.itemSize;o<l;o++)this.array[e+o]=t.array[r+o];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,r=this.count;t<r;t++)El.fromBufferAttribute(this,t),El.applyMatrix3(e),this.setXY(t,El.x,El.y);else if(this.itemSize===3)for(let t=0,r=this.count;t<r;t++)nn.fromBufferAttribute(this,t),nn.applyMatrix3(e),this.setXYZ(t,nn.x,nn.y,nn.z);return this}applyMatrix4(e){for(let t=0,r=this.count;t<r;t++)nn.fromBufferAttribute(this,t),nn.applyMatrix4(e),this.setXYZ(t,nn.x,nn.y,nn.z);return this}applyNormalMatrix(e){for(let t=0,r=this.count;t<r;t++)nn.fromBufferAttribute(this,t),nn.applyNormalMatrix(e),this.setXYZ(t,nn.x,nn.y,nn.z);return this}transformDirection(e){for(let t=0,r=this.count;t<r;t++)nn.fromBufferAttribute(this,t),nn.transformDirection(e),this.setXYZ(t,nn.x,nn.y,nn.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let r=this.array[e*this.itemSize+t];return this.normalized&&(r=Ho(r,this.array)),r}setComponent(e,t,r){return this.normalized&&(r=Hn(r,this.array)),this.array[e*this.itemSize+t]=r,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Ho(t,this.array)),t}setX(e,t){return this.normalized&&(t=Hn(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Ho(t,this.array)),t}setY(e,t){return this.normalized&&(t=Hn(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Ho(t,this.array)),t}setZ(e,t){return this.normalized&&(t=Hn(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Ho(t,this.array)),t}setW(e,t){return this.normalized&&(t=Hn(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,r){return e*=this.itemSize,this.normalized&&(t=Hn(t,this.array),r=Hn(r,this.array)),this.array[e+0]=t,this.array[e+1]=r,this}setXYZ(e,t,r,o){return e*=this.itemSize,this.normalized&&(t=Hn(t,this.array),r=Hn(r,this.array),o=Hn(o,this.array)),this.array[e+0]=t,this.array[e+1]=r,this.array[e+2]=o,this}setXYZW(e,t,r,o,l){return e*=this.itemSize,this.normalized&&(t=Hn(t,this.array),r=Hn(r,this.array),o=Hn(o,this.array),l=Hn(l,this.array)),this.array[e+0]=t,this.array[e+1]=r,this.array[e+2]=o,this.array[e+3]=l,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==Mm&&(e.usage=this.usage),e}}class Z0 extends Ti{constructor(e,t,r){super(new Uint16Array(e),t,r)}}class J0 extends Ti{constructor(e,t,r){super(new Uint32Array(e),t,r)}}class In extends Ti{constructor(e,t,r){super(new Float32Array(e),t,r)}}let Zx=0;const ii=new $t,lf=new _n,Vs=new Q,Kn=new la,Xo=new la,mn=new Q;class Ci extends so{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Zx++}),this.uuid=oo(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(q0(e)?J0:Z0)(e,1):this.index=e,this}setIndirect(e){return this.indirect=e,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,r=0){this.groups.push({start:e,count:t,materialIndex:r})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const r=this.attributes.normal;if(r!==void 0){const l=new Et().getNormalMatrix(e);r.applyNormalMatrix(l),r.needsUpdate=!0}const o=this.attributes.tangent;return o!==void 0&&(o.transformDirection(e),o.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return ii.makeRotationFromQuaternion(e),this.applyMatrix4(ii),this}rotateX(e){return ii.makeRotationX(e),this.applyMatrix4(ii),this}rotateY(e){return ii.makeRotationY(e),this.applyMatrix4(ii),this}rotateZ(e){return ii.makeRotationZ(e),this.applyMatrix4(ii),this}translate(e,t,r){return ii.makeTranslation(e,t,r),this.applyMatrix4(ii),this}scale(e,t,r){return ii.makeScale(e,t,r),this.applyMatrix4(ii),this}lookAt(e){return lf.lookAt(e),lf.updateMatrix(),this.applyMatrix4(lf.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(Vs).negate(),this.translate(Vs.x,Vs.y,Vs.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const r=[];for(let o=0,l=e.length;o<l;o++){const u=e[o];r.push(u.x,u.y,u.z||0)}this.setAttribute("position",new In(r,3))}else{const r=Math.min(e.length,t.count);for(let o=0;o<r;o++){const l=e[o];t.setXYZ(o,l.x,l.y,l.z||0)}e.length>t.count&&console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new la);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new Q(-1/0,-1/0,-1/0),new Q(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let r=0,o=t.length;r<o;r++){const l=t[r];Kn.setFromBufferAttribute(l),this.morphTargetsRelative?(mn.addVectors(this.boundingBox.min,Kn.min),this.boundingBox.expandByPoint(mn),mn.addVectors(this.boundingBox.max,Kn.max),this.boundingBox.expandByPoint(mn)):(this.boundingBox.expandByPoint(Kn.min),this.boundingBox.expandByPoint(Kn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Ad);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new Q,1/0);return}if(e){const r=this.boundingSphere.center;if(Kn.setFromBufferAttribute(e),t)for(let l=0,u=t.length;l<u;l++){const f=t[l];Xo.setFromBufferAttribute(f),this.morphTargetsRelative?(mn.addVectors(Kn.min,Xo.min),Kn.expandByPoint(mn),mn.addVectors(Kn.max,Xo.max),Kn.expandByPoint(mn)):(Kn.expandByPoint(Xo.min),Kn.expandByPoint(Xo.max))}Kn.getCenter(r);let o=0;for(let l=0,u=e.count;l<u;l++)mn.fromBufferAttribute(e,l),o=Math.max(o,r.distanceToSquared(mn));if(t)for(let l=0,u=t.length;l<u;l++){const f=t[l],d=this.morphTargetsRelative;for(let p=0,v=f.count;p<v;p++)mn.fromBufferAttribute(f,p),d&&(Vs.fromBufferAttribute(e,p),mn.add(Vs)),o=Math.max(o,r.distanceToSquared(mn))}this.boundingSphere.radius=Math.sqrt(o),isNaN(this.boundingSphere.radius)&&console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const r=t.position,o=t.normal,l=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Ti(new Float32Array(4*r.count),4));const u=this.getAttribute("tangent"),f=[],d=[];for(let N=0;N<r.count;N++)f[N]=new Q,d[N]=new Q;const p=new Q,v=new Q,g=new Q,_=new Ge,S=new Ge,M=new Ge,A=new Q,y=new Q;function x(N,C,T){p.fromBufferAttribute(r,N),v.fromBufferAttribute(r,C),g.fromBufferAttribute(r,T),_.fromBufferAttribute(l,N),S.fromBufferAttribute(l,C),M.fromBufferAttribute(l,T),v.sub(p),g.sub(p),S.sub(_),M.sub(_);const F=1/(S.x*M.y-M.x*S.y);isFinite(F)&&(A.copy(v).multiplyScalar(M.y).addScaledVector(g,-S.y).multiplyScalar(F),y.copy(g).multiplyScalar(S.x).addScaledVector(v,-M.x).multiplyScalar(F),f[N].add(A),f[C].add(A),f[T].add(A),d[N].add(y),d[C].add(y),d[T].add(y))}let O=this.groups;O.length===0&&(O=[{start:0,count:e.count}]);for(let N=0,C=O.length;N<C;++N){const T=O[N],F=T.start,$=T.count;for(let ee=F,le=F+$;ee<le;ee+=3)x(e.getX(ee+0),e.getX(ee+1),e.getX(ee+2))}const D=new Q,R=new Q,z=new Q,H=new Q;function I(N){z.fromBufferAttribute(o,N),H.copy(z);const C=f[N];D.copy(C),D.sub(z.multiplyScalar(z.dot(C))).normalize(),R.crossVectors(H,C);const F=R.dot(d[N])<0?-1:1;u.setXYZW(N,D.x,D.y,D.z,F)}for(let N=0,C=O.length;N<C;++N){const T=O[N],F=T.start,$=T.count;for(let ee=F,le=F+$;ee<le;ee+=3)I(e.getX(ee+0)),I(e.getX(ee+1)),I(e.getX(ee+2))}}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let r=this.getAttribute("normal");if(r===void 0)r=new Ti(new Float32Array(t.count*3),3),this.setAttribute("normal",r);else for(let _=0,S=r.count;_<S;_++)r.setXYZ(_,0,0,0);const o=new Q,l=new Q,u=new Q,f=new Q,d=new Q,p=new Q,v=new Q,g=new Q;if(e)for(let _=0,S=e.count;_<S;_+=3){const M=e.getX(_+0),A=e.getX(_+1),y=e.getX(_+2);o.fromBufferAttribute(t,M),l.fromBufferAttribute(t,A),u.fromBufferAttribute(t,y),v.subVectors(u,l),g.subVectors(o,l),v.cross(g),f.fromBufferAttribute(r,M),d.fromBufferAttribute(r,A),p.fromBufferAttribute(r,y),f.add(v),d.add(v),p.add(v),r.setXYZ(M,f.x,f.y,f.z),r.setXYZ(A,d.x,d.y,d.z),r.setXYZ(y,p.x,p.y,p.z)}else for(let _=0,S=t.count;_<S;_+=3)o.fromBufferAttribute(t,_+0),l.fromBufferAttribute(t,_+1),u.fromBufferAttribute(t,_+2),v.subVectors(u,l),g.subVectors(o,l),v.cross(g),r.setXYZ(_+0,v.x,v.y,v.z),r.setXYZ(_+1,v.x,v.y,v.z),r.setXYZ(_+2,v.x,v.y,v.z);this.normalizeNormals(),r.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,r=e.count;t<r;t++)mn.fromBufferAttribute(e,t),mn.normalize(),e.setXYZ(t,mn.x,mn.y,mn.z)}toNonIndexed(){function e(f,d){const p=f.array,v=f.itemSize,g=f.normalized,_=new p.constructor(d.length*v);let S=0,M=0;for(let A=0,y=d.length;A<y;A++){f.isInterleavedBufferAttribute?S=d[A]*f.data.stride+f.offset:S=d[A]*v;for(let x=0;x<v;x++)_[M++]=p[S++]}return new Ti(_,v,g)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new Ci,r=this.index.array,o=this.attributes;for(const f in o){const d=o[f],p=e(d,r);t.setAttribute(f,p)}const l=this.morphAttributes;for(const f in l){const d=[],p=l[f];for(let v=0,g=p.length;v<g;v++){const _=p[v],S=e(_,r);d.push(S)}t.morphAttributes[f]=d}t.morphTargetsRelative=this.morphTargetsRelative;const u=this.groups;for(let f=0,d=u.length;f<d;f++){const p=u[f];t.addGroup(p.start,p.count,p.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const d=this.parameters;for(const p in d)d[p]!==void 0&&(e[p]=d[p]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const r=this.attributes;for(const d in r){const p=r[d];e.data.attributes[d]=p.toJSON(e.data)}const o={};let l=!1;for(const d in this.morphAttributes){const p=this.morphAttributes[d],v=[];for(let g=0,_=p.length;g<_;g++){const S=p[g];v.push(S.toJSON(e.data))}v.length>0&&(o[d]=v,l=!0)}l&&(e.data.morphAttributes=o,e.data.morphTargetsRelative=this.morphTargetsRelative);const u=this.groups;u.length>0&&(e.data.groups=JSON.parse(JSON.stringify(u)));const f=this.boundingSphere;return f!==null&&(e.data.boundingSphere=f.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const r=e.index;r!==null&&this.setIndex(r.clone());const o=e.attributes;for(const p in o){const v=o[p];this.setAttribute(p,v.clone(t))}const l=e.morphAttributes;for(const p in l){const v=[],g=l[p];for(let _=0,S=g.length;_<S;_++)v.push(g[_].clone(t));this.morphAttributes[p]=v}this.morphTargetsRelative=e.morphTargetsRelative;const u=e.groups;for(let p=0,v=u.length;p<v;p++){const g=u[p];this.addGroup(g.start,g.count,g.materialIndex)}const f=e.boundingBox;f!==null&&(this.boundingBox=f.clone());const d=e.boundingSphere;return d!==null&&(this.boundingSphere=d.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}const Fm=new $t,Yr=new $0,wl=new Ad,Om=new Q,Tl=new Q,Al=new Q,Rl=new Q,cf=new Q,Cl=new Q,km=new Q,bl=new Q;class an extends _n{constructor(e=new Ci,t=new Jl){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,r=Object.keys(t);if(r.length>0){const o=t[r[0]];if(o!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let l=0,u=o.length;l<u;l++){const f=o[l].name||String(l);this.morphTargetInfluences.push(0),this.morphTargetDictionary[f]=l}}}}getVertexPosition(e,t){const r=this.geometry,o=r.attributes.position,l=r.morphAttributes.position,u=r.morphTargetsRelative;t.fromBufferAttribute(o,e);const f=this.morphTargetInfluences;if(l&&f){Cl.set(0,0,0);for(let d=0,p=l.length;d<p;d++){const v=f[d],g=l[d];v!==0&&(cf.fromBufferAttribute(g,e),u?Cl.addScaledVector(cf,v):Cl.addScaledVector(cf.sub(t),v))}t.add(Cl)}return t}raycast(e,t){const r=this.geometry,o=this.material,l=this.matrixWorld;o!==void 0&&(r.boundingSphere===null&&r.computeBoundingSphere(),wl.copy(r.boundingSphere),wl.applyMatrix4(l),Yr.copy(e.ray).recast(e.near),!(wl.containsPoint(Yr.origin)===!1&&(Yr.intersectSphere(wl,Om)===null||Yr.origin.distanceToSquared(Om)>(e.far-e.near)**2))&&(Fm.copy(l).invert(),Yr.copy(e.ray).applyMatrix4(Fm),!(r.boundingBox!==null&&Yr.intersectsBox(r.boundingBox)===!1)&&this._computeIntersections(e,t,Yr)))}_computeIntersections(e,t,r){let o;const l=this.geometry,u=this.material,f=l.index,d=l.attributes.position,p=l.attributes.uv,v=l.attributes.uv1,g=l.attributes.normal,_=l.groups,S=l.drawRange;if(f!==null)if(Array.isArray(u))for(let M=0,A=_.length;M<A;M++){const y=_[M],x=u[y.materialIndex],O=Math.max(y.start,S.start),D=Math.min(f.count,Math.min(y.start+y.count,S.start+S.count));for(let R=O,z=D;R<z;R+=3){const H=f.getX(R),I=f.getX(R+1),N=f.getX(R+2);o=Pl(this,x,e,r,p,v,g,H,I,N),o&&(o.faceIndex=Math.floor(R/3),o.face.materialIndex=y.materialIndex,t.push(o))}}else{const M=Math.max(0,S.start),A=Math.min(f.count,S.start+S.count);for(let y=M,x=A;y<x;y+=3){const O=f.getX(y),D=f.getX(y+1),R=f.getX(y+2);o=Pl(this,u,e,r,p,v,g,O,D,R),o&&(o.faceIndex=Math.floor(y/3),t.push(o))}}else if(d!==void 0)if(Array.isArray(u))for(let M=0,A=_.length;M<A;M++){const y=_[M],x=u[y.materialIndex],O=Math.max(y.start,S.start),D=Math.min(d.count,Math.min(y.start+y.count,S.start+S.count));for(let R=O,z=D;R<z;R+=3){const H=R,I=R+1,N=R+2;o=Pl(this,x,e,r,p,v,g,H,I,N),o&&(o.faceIndex=Math.floor(R/3),o.face.materialIndex=y.materialIndex,t.push(o))}}else{const M=Math.max(0,S.start),A=Math.min(d.count,S.start+S.count);for(let y=M,x=A;y<x;y+=3){const O=y,D=y+1,R=y+2;o=Pl(this,u,e,r,p,v,g,O,D,R),o&&(o.faceIndex=Math.floor(y/3),t.push(o))}}}}function Jx(s,e,t,r,o,l,u,f){let d;if(e.side===Gn?d=r.intersectTriangle(u,l,o,!0,f):d=r.intersectTriangle(o,l,u,e.side===Cr,f),d===null)return null;bl.copy(f),bl.applyMatrix4(s.matrixWorld);const p=t.ray.origin.distanceTo(bl);return p<t.near||p>t.far?null:{distance:p,point:bl.clone(),object:s}}function Pl(s,e,t,r,o,l,u,f,d,p){s.getVertexPosition(f,Tl),s.getVertexPosition(d,Al),s.getVertexPosition(p,Rl);const v=Jx(s,e,t,r,Tl,Al,Rl,km);if(v){const g=new Q;mi.getBarycoord(km,Tl,Al,Rl,g),o&&(v.uv=mi.getInterpolatedAttribute(o,f,d,p,g,new Ge)),l&&(v.uv1=mi.getInterpolatedAttribute(l,f,d,p,g,new Ge)),u&&(v.normal=mi.getInterpolatedAttribute(u,f,d,p,g,new Q),v.normal.dot(r.direction)>0&&v.normal.multiplyScalar(-1));const _={a:f,b:d,c:p,normal:new Q,materialIndex:0};mi.getNormal(Tl,Al,Rl,_.normal),v.face=_,v.barycoord=g}return v}class ji extends Ci{constructor(e=1,t=1,r=1,o=1,l=1,u=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:r,widthSegments:o,heightSegments:l,depthSegments:u};const f=this;o=Math.floor(o),l=Math.floor(l),u=Math.floor(u);const d=[],p=[],v=[],g=[];let _=0,S=0;M("z","y","x",-1,-1,r,t,e,u,l,0),M("z","y","x",1,-1,r,t,-e,u,l,1),M("x","z","y",1,1,e,r,t,o,u,2),M("x","z","y",1,-1,e,r,-t,o,u,3),M("x","y","z",1,-1,e,t,r,o,l,4),M("x","y","z",-1,-1,e,t,-r,o,l,5),this.setIndex(d),this.setAttribute("position",new In(p,3)),this.setAttribute("normal",new In(v,3)),this.setAttribute("uv",new In(g,2));function M(A,y,x,O,D,R,z,H,I,N,C){const T=R/I,F=z/N,$=R/2,ee=z/2,le=H/2,ne=I+1,ce=N+1;let re=0,V=0;const me=new Q;for(let ie=0;ie<ce;ie++){const P=ie*F-ee;for(let B=0;B<ne;B++){const Z=B*T-$;me[A]=Z*O,me[y]=P*D,me[x]=le,p.push(me.x,me.y,me.z),me[A]=0,me[y]=0,me[x]=H>0?1:-1,v.push(me.x,me.y,me.z),g.push(B/I),g.push(1-ie/N),re+=1}}for(let ie=0;ie<N;ie++)for(let P=0;P<I;P++){const B=_+P+ne*ie,Z=_+P+ne*(ie+1),ue=_+(P+1)+ne*(ie+1),he=_+(P+1)+ne*ie;d.push(B,Z,he),d.push(Z,ue,he),V+=6}f.addGroup(S,V,C),S+=V,_+=re}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ji(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}function no(s){const e={};for(const t in s){e[t]={};for(const r in s[t]){const o=s[t][r];o&&(o.isColor||o.isMatrix3||o.isMatrix4||o.isVector2||o.isVector3||o.isVector4||o.isTexture||o.isQuaternion)?o.isRenderTargetTexture?(console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][r]=null):e[t][r]=o.clone():Array.isArray(o)?e[t][r]=o.slice():e[t][r]=o}}return e}function Dn(s){const e={};for(let t=0;t<s.length;t++){const r=no(s[t]);for(const o in r)e[o]=r[o]}return e}function Qx(s){const e=[];for(let t=0;t<s.length;t++)e.push(s[t].clone());return e}function Q0(s){const e=s.getRenderTarget();return e===null?s.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:Nt.workingColorSpace}const ey={clone:no,merge:Dn};var ty=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,ny=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class br extends ca{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=ty,this.fragmentShader=ny,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=no(e.uniforms),this.uniformsGroups=Qx(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const o in this.uniforms){const u=this.uniforms[o].value;u&&u.isTexture?t.uniforms[o]={type:"t",value:u.toJSON(e).uuid}:u&&u.isColor?t.uniforms[o]={type:"c",value:u.getHex()}:u&&u.isVector2?t.uniforms[o]={type:"v2",value:u.toArray()}:u&&u.isVector3?t.uniforms[o]={type:"v3",value:u.toArray()}:u&&u.isVector4?t.uniforms[o]={type:"v4",value:u.toArray()}:u&&u.isMatrix3?t.uniforms[o]={type:"m3",value:u.toArray()}:u&&u.isMatrix4?t.uniforms[o]={type:"m4",value:u.toArray()}:t.uniforms[o]={value:u}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const r={};for(const o in this.extensions)this.extensions[o]===!0&&(r[o]=!0);return Object.keys(r).length>0&&(t.extensions=r),t}}class eg extends _n{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new $t,this.projectionMatrix=new $t,this.projectionMatrixInverse=new $t,this.coordinateSystem=wi,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}}const wr=new Q,Bm=new Ge,zm=new Ge;class ri extends eg{constructor(e=50,t=1,r=.1,o=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=r,this.far=o,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=cd*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Hu*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return cd*2*Math.atan(Math.tan(Hu*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,r){wr.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(wr.x,wr.y).multiplyScalar(-e/wr.z),wr.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),r.set(wr.x,wr.y).multiplyScalar(-e/wr.z)}getViewSize(e,t){return this.getViewBounds(e,Bm,zm),t.subVectors(zm,Bm)}setViewOffset(e,t,r,o,l,u){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=r,this.view.offsetY=o,this.view.width=l,this.view.height=u,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(Hu*.5*this.fov)/this.zoom,r=2*t,o=this.aspect*r,l=-.5*o;const u=this.view;if(this.view!==null&&this.view.enabled){const d=u.fullWidth,p=u.fullHeight;l+=u.offsetX*o/d,t-=u.offsetY*r/p,o*=u.width/d,r*=u.height/p}const f=this.filmOffset;f!==0&&(l+=e*f/this.getFilmWidth()),this.projectionMatrix.makePerspective(l,l+o,t,t-r,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}const Gs=-90,Ws=1;class iy extends _n{constructor(e,t,r){super(),this.type="CubeCamera",this.renderTarget=r,this.coordinateSystem=null,this.activeMipmapLevel=0;const o=new ri(Gs,Ws,e,t);o.layers=this.layers,this.add(o);const l=new ri(Gs,Ws,e,t);l.layers=this.layers,this.add(l);const u=new ri(Gs,Ws,e,t);u.layers=this.layers,this.add(u);const f=new ri(Gs,Ws,e,t);f.layers=this.layers,this.add(f);const d=new ri(Gs,Ws,e,t);d.layers=this.layers,this.add(d);const p=new ri(Gs,Ws,e,t);p.layers=this.layers,this.add(p)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[r,o,l,u,f,d]=t;for(const p of t)this.remove(p);if(e===wi)r.up.set(0,1,0),r.lookAt(1,0,0),o.up.set(0,1,0),o.lookAt(-1,0,0),l.up.set(0,0,-1),l.lookAt(0,1,0),u.up.set(0,0,1),u.lookAt(0,-1,0),f.up.set(0,1,0),f.lookAt(0,0,1),d.up.set(0,1,0),d.lookAt(0,0,-1);else if(e===Kl)r.up.set(0,-1,0),r.lookAt(-1,0,0),o.up.set(0,-1,0),o.lookAt(1,0,0),l.up.set(0,0,1),l.lookAt(0,1,0),u.up.set(0,0,-1),u.lookAt(0,-1,0),f.up.set(0,-1,0),f.lookAt(0,0,1),d.up.set(0,-1,0),d.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const p of t)this.add(p),p.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:r,activeMipmapLevel:o}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[l,u,f,d,p,v]=this.children,g=e.getRenderTarget(),_=e.getActiveCubeFace(),S=e.getActiveMipmapLevel(),M=e.xr.enabled;e.xr.enabled=!1;const A=r.texture.generateMipmaps;r.texture.generateMipmaps=!1,e.setRenderTarget(r,0,o),e.render(t,l),e.setRenderTarget(r,1,o),e.render(t,u),e.setRenderTarget(r,2,o),e.render(t,f),e.setRenderTarget(r,3,o),e.render(t,d),e.setRenderTarget(r,4,o),e.render(t,p),r.texture.generateMipmaps=A,e.setRenderTarget(r,5,o),e.render(t,v),e.setRenderTarget(g,_,S),e.xr.enabled=M,r.texture.needsPMREMUpdate=!0}}class tg extends Nn{constructor(e=[],t=Qs,r,o,l,u,f,d,p,v){super(e,t,r,o,l,u,f,d,p,v),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class ry extends os{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const r={width:e,height:e,depth:1},o=[r,r,r,r,r,r];this.texture=new tg(o),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const r={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},o=new ji(5,5,5),l=new br({name:"CubemapFromEquirect",uniforms:no(r.uniforms),vertexShader:r.vertexShader,fragmentShader:r.fragmentShader,side:Gn,blending:Ar});l.uniforms.tEquirect.value=t;const u=new an(o,l),f=t.minFilter;return t.minFilter===rs&&(t.minFilter=Ei),new iy(1,10,this).update(e,u),t.minFilter=f,u.geometry.dispose(),u.material.dispose(),this}clear(e,t=!0,r=!0,o=!0){const l=e.getRenderTarget();for(let u=0;u<6;u++)e.setRenderTarget(this,u),e.clear(t,r,o);e.setRenderTarget(l)}}class jo extends _n{constructor(){super(),this.isGroup=!0,this.type="Group"}}const sy={type:"move"};class uf{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new jo,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new jo,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new Q,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new Q),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new jo,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new Q,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new Q),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const r of e.hand.values())this._getHandJoint(t,r)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,r){let o=null,l=null,u=null;const f=this._targetRay,d=this._grip,p=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(p&&e.hand){u=!0;for(const A of e.hand.values()){const y=t.getJointPose(A,r),x=this._getHandJoint(p,A);y!==null&&(x.matrix.fromArray(y.transform.matrix),x.matrix.decompose(x.position,x.rotation,x.scale),x.matrixWorldNeedsUpdate=!0,x.jointRadius=y.radius),x.visible=y!==null}const v=p.joints["index-finger-tip"],g=p.joints["thumb-tip"],_=v.position.distanceTo(g.position),S=.02,M=.005;p.inputState.pinching&&_>S+M?(p.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!p.inputState.pinching&&_<=S-M&&(p.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else d!==null&&e.gripSpace&&(l=t.getPose(e.gripSpace,r),l!==null&&(d.matrix.fromArray(l.transform.matrix),d.matrix.decompose(d.position,d.rotation,d.scale),d.matrixWorldNeedsUpdate=!0,l.linearVelocity?(d.hasLinearVelocity=!0,d.linearVelocity.copy(l.linearVelocity)):d.hasLinearVelocity=!1,l.angularVelocity?(d.hasAngularVelocity=!0,d.angularVelocity.copy(l.angularVelocity)):d.hasAngularVelocity=!1));f!==null&&(o=t.getPose(e.targetRaySpace,r),o===null&&l!==null&&(o=l),o!==null&&(f.matrix.fromArray(o.transform.matrix),f.matrix.decompose(f.position,f.rotation,f.scale),f.matrixWorldNeedsUpdate=!0,o.linearVelocity?(f.hasLinearVelocity=!0,f.linearVelocity.copy(o.linearVelocity)):f.hasLinearVelocity=!1,o.angularVelocity?(f.hasAngularVelocity=!0,f.angularVelocity.copy(o.angularVelocity)):f.hasAngularVelocity=!1,this.dispatchEvent(sy)))}return f!==null&&(f.visible=o!==null),d!==null&&(d.visible=l!==null),p!==null&&(p.visible=u!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const r=new jo;r.matrixAutoUpdate=!1,r.visible=!1,e.joints[t.jointName]=r,e.add(r)}return e.joints[t.jointName]}}class oy extends _n{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Ri,this.environmentIntensity=1,this.environmentRotation=new Ri,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const ff=new Q,ay=new Q,ly=new Et;class Jr{constructor(e=new Q(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,r,o){return this.normal.set(e,t,r),this.constant=o,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,r){const o=ff.subVectors(r,t).cross(ay.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(o,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t){const r=e.delta(ff),o=this.normal.dot(r);if(o===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const l=-(e.start.dot(this.normal)+this.constant)/o;return l<0||l>1?null:t.copy(e.start).addScaledVector(r,l)}intersectsLine(e){const t=this.distanceToPoint(e.start),r=this.distanceToPoint(e.end);return t<0&&r>0||r<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const r=t||ly.getNormalMatrix(e),o=this.coplanarPoint(ff).applyMatrix4(e),l=this.normal.applyMatrix3(r).normalize();return this.constant=-o.dot(l),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const $r=new Ad,cy=new Ge(.5,.5),Ll=new Q;class Cd{constructor(e=new Jr,t=new Jr,r=new Jr,o=new Jr,l=new Jr,u=new Jr){this.planes=[e,t,r,o,l,u]}set(e,t,r,o,l,u){const f=this.planes;return f[0].copy(e),f[1].copy(t),f[2].copy(r),f[3].copy(o),f[4].copy(l),f[5].copy(u),this}copy(e){const t=this.planes;for(let r=0;r<6;r++)t[r].copy(e.planes[r]);return this}setFromProjectionMatrix(e,t=wi,r=!1){const o=this.planes,l=e.elements,u=l[0],f=l[1],d=l[2],p=l[3],v=l[4],g=l[5],_=l[6],S=l[7],M=l[8],A=l[9],y=l[10],x=l[11],O=l[12],D=l[13],R=l[14],z=l[15];if(o[0].setComponents(p-u,S-v,x-M,z-O).normalize(),o[1].setComponents(p+u,S+v,x+M,z+O).normalize(),o[2].setComponents(p+f,S+g,x+A,z+D).normalize(),o[3].setComponents(p-f,S-g,x-A,z-D).normalize(),r)o[4].setComponents(d,_,y,R).normalize(),o[5].setComponents(p-d,S-_,x-y,z-R).normalize();else if(o[4].setComponents(p-d,S-_,x-y,z-R).normalize(),t===wi)o[5].setComponents(p+d,S+_,x+y,z+R).normalize();else if(t===Kl)o[5].setComponents(d,_,y,R).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),$r.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),$r.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere($r)}intersectsSprite(e){$r.center.set(0,0,0);const t=cy.distanceTo(e.center);return $r.radius=.7071067811865476+t,$r.applyMatrix4(e.matrixWorld),this.intersectsSphere($r)}intersectsSphere(e){const t=this.planes,r=e.center,o=-e.radius;for(let l=0;l<6;l++)if(t[l].distanceToPoint(r)<o)return!1;return!0}intersectsBox(e){const t=this.planes;for(let r=0;r<6;r++){const o=t[r];if(Ll.x=o.normal.x>0?e.max.x:e.min.x,Ll.y=o.normal.y>0?e.max.y:e.min.y,Ll.z=o.normal.z>0?e.max.z:e.min.z,o.distanceToPoint(Ll)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let r=0;r<6;r++)if(t[r].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class uy extends Nn{constructor(e,t,r,o,l,u,f,d,p){super(e,t,r,o,l,u,f,d,p),this.isCanvasTexture=!0,this.needsUpdate=!0}}class ng extends Nn{constructor(e,t,r=ss,o,l,u,f=vi,d=vi,p,v=ea,g=1){if(v!==ea&&v!==ta)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const _={width:e,height:t,depth:g};super(_,o,l,u,f,d,v,r,p),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Td(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class ig extends Nn{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class Ql extends Ci{constructor(e=1,t=1,r=1,o=32,l=1,u=!1,f=0,d=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:r,radialSegments:o,heightSegments:l,openEnded:u,thetaStart:f,thetaLength:d};const p=this;o=Math.floor(o),l=Math.floor(l);const v=[],g=[],_=[],S=[];let M=0;const A=[],y=r/2;let x=0;O(),u===!1&&(e>0&&D(!0),t>0&&D(!1)),this.setIndex(v),this.setAttribute("position",new In(g,3)),this.setAttribute("normal",new In(_,3)),this.setAttribute("uv",new In(S,2));function O(){const R=new Q,z=new Q;let H=0;const I=(t-e)/r;for(let N=0;N<=l;N++){const C=[],T=N/l,F=T*(t-e)+e;for(let $=0;$<=o;$++){const ee=$/o,le=ee*d+f,ne=Math.sin(le),ce=Math.cos(le);z.x=F*ne,z.y=-T*r+y,z.z=F*ce,g.push(z.x,z.y,z.z),R.set(ne,I,ce).normalize(),_.push(R.x,R.y,R.z),S.push(ee,1-T),C.push(M++)}A.push(C)}for(let N=0;N<o;N++)for(let C=0;C<l;C++){const T=A[C][N],F=A[C+1][N],$=A[C+1][N+1],ee=A[C][N+1];(e>0||C!==0)&&(v.push(T,F,ee),H+=3),(t>0||C!==l-1)&&(v.push(F,$,ee),H+=3)}p.addGroup(x,H,0),x+=H}function D(R){const z=M,H=new Ge,I=new Q;let N=0;const C=R===!0?e:t,T=R===!0?1:-1;for(let $=1;$<=o;$++)g.push(0,y*T,0),_.push(0,T,0),S.push(.5,.5),M++;const F=M;for(let $=0;$<=o;$++){const le=$/o*d+f,ne=Math.cos(le),ce=Math.sin(le);I.x=C*ce,I.y=y*T,I.z=C*ne,g.push(I.x,I.y,I.z),_.push(0,T,0),H.x=ne*.5+.5,H.y=ce*.5*T+.5,S.push(H.x,H.y),M++}for(let $=0;$<o;$++){const ee=z+$,le=F+$;R===!0?v.push(le,le+1,ee):v.push(le+1,le,ee),N+=3}p.addGroup(x,N,R===!0?1:2),x+=N}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Ql(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}}class bi{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){console.warn("THREE.Curve: .getPoint() not implemented.")}getPointAt(e,t){const r=this.getUtoTmapping(e);return this.getPoint(r,t)}getPoints(e=5){const t=[];for(let r=0;r<=e;r++)t.push(this.getPoint(r/e));return t}getSpacedPoints(e=5){const t=[];for(let r=0;r<=e;r++)t.push(this.getPointAt(r/e));return t}getLength(){const e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;const t=[];let r,o=this.getPoint(0),l=0;t.push(0);for(let u=1;u<=e;u++)r=this.getPoint(u/e),l+=r.distanceTo(o),t.push(l),o=r;return this.cacheArcLengths=t,t}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,t=null){const r=this.getLengths();let o=0;const l=r.length;let u;t?u=t:u=e*r[l-1];let f=0,d=l-1,p;for(;f<=d;)if(o=Math.floor(f+(d-f)/2),p=r[o]-u,p<0)f=o+1;else if(p>0)d=o-1;else{d=o;break}if(o=d,r[o]===u)return o/(l-1);const v=r[o],_=r[o+1]-v,S=(u-v)/_;return(o+S)/(l-1)}getTangent(e,t){let o=e-1e-4,l=e+1e-4;o<0&&(o=0),l>1&&(l=1);const u=this.getPoint(o),f=this.getPoint(l),d=t||(u.isVector2?new Ge:new Q);return d.copy(f).sub(u).normalize(),d}getTangentAt(e,t){const r=this.getUtoTmapping(e);return this.getTangent(r,t)}computeFrenetFrames(e,t=!1){const r=new Q,o=[],l=[],u=[],f=new Q,d=new $t;for(let S=0;S<=e;S++){const M=S/e;o[S]=this.getTangentAt(M,new Q)}l[0]=new Q,u[0]=new Q;let p=Number.MAX_VALUE;const v=Math.abs(o[0].x),g=Math.abs(o[0].y),_=Math.abs(o[0].z);v<=p&&(p=v,r.set(1,0,0)),g<=p&&(p=g,r.set(0,1,0)),_<=p&&r.set(0,0,1),f.crossVectors(o[0],r).normalize(),l[0].crossVectors(o[0],f),u[0].crossVectors(o[0],l[0]);for(let S=1;S<=e;S++){if(l[S]=l[S-1].clone(),u[S]=u[S-1].clone(),f.crossVectors(o[S-1],o[S]),f.length()>Number.EPSILON){f.normalize();const M=Math.acos(Ct(o[S-1].dot(o[S]),-1,1));l[S].applyMatrix4(d.makeRotationAxis(f,M))}u[S].crossVectors(o[S],l[S])}if(t===!0){let S=Math.acos(Ct(l[0].dot(l[e]),-1,1));S/=e,o[0].dot(f.crossVectors(l[0],l[e]))>0&&(S=-S);for(let M=1;M<=e;M++)l[M].applyMatrix4(d.makeRotationAxis(o[M],S*M)),u[M].crossVectors(o[M],l[M])}return{tangents:o,normals:l,binormals:u}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){const e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}}class bd extends bi{constructor(e=0,t=0,r=1,o=1,l=0,u=Math.PI*2,f=!1,d=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=e,this.aY=t,this.xRadius=r,this.yRadius=o,this.aStartAngle=l,this.aEndAngle=u,this.aClockwise=f,this.aRotation=d}getPoint(e,t=new Ge){const r=t,o=Math.PI*2;let l=this.aEndAngle-this.aStartAngle;const u=Math.abs(l)<Number.EPSILON;for(;l<0;)l+=o;for(;l>o;)l-=o;l<Number.EPSILON&&(u?l=0:l=o),this.aClockwise===!0&&!u&&(l===o?l=-o:l=l-o);const f=this.aStartAngle+e*l;let d=this.aX+this.xRadius*Math.cos(f),p=this.aY+this.yRadius*Math.sin(f);if(this.aRotation!==0){const v=Math.cos(this.aRotation),g=Math.sin(this.aRotation),_=d-this.aX,S=p-this.aY;d=_*v-S*g+this.aX,p=_*g+S*v+this.aY}return r.set(d,p)}copy(e){return super.copy(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}toJSON(){const e=super.toJSON();return e.aX=this.aX,e.aY=this.aY,e.xRadius=this.xRadius,e.yRadius=this.yRadius,e.aStartAngle=this.aStartAngle,e.aEndAngle=this.aEndAngle,e.aClockwise=this.aClockwise,e.aRotation=this.aRotation,e}fromJSON(e){return super.fromJSON(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}}class fy extends bd{constructor(e,t,r,o,l,u){super(e,t,r,r,o,l,u),this.isArcCurve=!0,this.type="ArcCurve"}}function Pd(){let s=0,e=0,t=0,r=0;function o(l,u,f,d){s=l,e=f,t=-3*l+3*u-2*f-d,r=2*l-2*u+f+d}return{initCatmullRom:function(l,u,f,d,p){o(u,f,p*(f-l),p*(d-u))},initNonuniformCatmullRom:function(l,u,f,d,p,v,g){let _=(u-l)/p-(f-l)/(p+v)+(f-u)/v,S=(f-u)/v-(d-u)/(v+g)+(d-f)/g;_*=v,S*=v,o(u,f,_,S)},calc:function(l){const u=l*l,f=u*l;return s+e*l+t*u+r*f}}}const Dl=new Q,df=new Pd,hf=new Pd,pf=new Pd;class dy extends bi{constructor(e=[],t=!1,r="centripetal",o=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=t,this.curveType=r,this.tension=o}getPoint(e,t=new Q){const r=t,o=this.points,l=o.length,u=(l-(this.closed?0:1))*e;let f=Math.floor(u),d=u-f;this.closed?f+=f>0?0:(Math.floor(Math.abs(f)/l)+1)*l:d===0&&f===l-1&&(f=l-2,d=1);let p,v;this.closed||f>0?p=o[(f-1)%l]:(Dl.subVectors(o[0],o[1]).add(o[0]),p=Dl);const g=o[f%l],_=o[(f+1)%l];if(this.closed||f+2<l?v=o[(f+2)%l]:(Dl.subVectors(o[l-1],o[l-2]).add(o[l-1]),v=Dl),this.curveType==="centripetal"||this.curveType==="chordal"){const S=this.curveType==="chordal"?.5:.25;let M=Math.pow(p.distanceToSquared(g),S),A=Math.pow(g.distanceToSquared(_),S),y=Math.pow(_.distanceToSquared(v),S);A<1e-4&&(A=1),M<1e-4&&(M=A),y<1e-4&&(y=A),df.initNonuniformCatmullRom(p.x,g.x,_.x,v.x,M,A,y),hf.initNonuniformCatmullRom(p.y,g.y,_.y,v.y,M,A,y),pf.initNonuniformCatmullRom(p.z,g.z,_.z,v.z,M,A,y)}else this.curveType==="catmullrom"&&(df.initCatmullRom(p.x,g.x,_.x,v.x,this.tension),hf.initCatmullRom(p.y,g.y,_.y,v.y,this.tension),pf.initCatmullRom(p.z,g.z,_.z,v.z,this.tension));return r.set(df.calc(d),hf.calc(d),pf.calc(d)),r}copy(e){super.copy(e),this.points=[];for(let t=0,r=e.points.length;t<r;t++){const o=e.points[t];this.points.push(o.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){const e=super.toJSON();e.points=[];for(let t=0,r=this.points.length;t<r;t++){const o=this.points[t];e.points.push(o.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,r=e.points.length;t<r;t++){const o=e.points[t];this.points.push(new Q().fromArray(o))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}}function Hm(s,e,t,r,o){const l=(r-e)*.5,u=(o-t)*.5,f=s*s,d=s*f;return(2*t-2*r+l+u)*d+(-3*t+3*r-2*l-u)*f+l*s+t}function hy(s,e){const t=1-s;return t*t*e}function py(s,e){return 2*(1-s)*s*e}function my(s,e){return s*s*e}function $o(s,e,t,r){return hy(s,e)+py(s,t)+my(s,r)}function gy(s,e){const t=1-s;return t*t*t*e}function vy(s,e){const t=1-s;return 3*t*t*s*e}function _y(s,e){return 3*(1-s)*s*s*e}function xy(s,e){return s*s*s*e}function Ko(s,e,t,r,o){return gy(s,e)+vy(s,t)+_y(s,r)+xy(s,o)}class rg extends bi{constructor(e=new Ge,t=new Ge,r=new Ge,o=new Ge){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=e,this.v1=t,this.v2=r,this.v3=o}getPoint(e,t=new Ge){const r=t,o=this.v0,l=this.v1,u=this.v2,f=this.v3;return r.set(Ko(e,o.x,l.x,u.x,f.x),Ko(e,o.y,l.y,u.y,f.y)),r}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}}class yy extends bi{constructor(e=new Q,t=new Q,r=new Q,o=new Q){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=e,this.v1=t,this.v2=r,this.v3=o}getPoint(e,t=new Q){const r=t,o=this.v0,l=this.v1,u=this.v2,f=this.v3;return r.set(Ko(e,o.x,l.x,u.x,f.x),Ko(e,o.y,l.y,u.y,f.y),Ko(e,o.z,l.z,u.z,f.z)),r}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}}class sg extends bi{constructor(e=new Ge,t=new Ge){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=e,this.v2=t}getPoint(e,t=new Ge){const r=t;return e===1?r.copy(this.v2):(r.copy(this.v2).sub(this.v1),r.multiplyScalar(e).add(this.v1)),r}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new Ge){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class Sy extends bi{constructor(e=new Q,t=new Q){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=e,this.v2=t}getPoint(e,t=new Q){const r=t;return e===1?r.copy(this.v2):(r.copy(this.v2).sub(this.v1),r.multiplyScalar(e).add(this.v1)),r}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new Q){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class og extends bi{constructor(e=new Ge,t=new Ge,r=new Ge){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=e,this.v1=t,this.v2=r}getPoint(e,t=new Ge){const r=t,o=this.v0,l=this.v1,u=this.v2;return r.set($o(e,o.x,l.x,u.x),$o(e,o.y,l.y,u.y)),r}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class My extends bi{constructor(e=new Q,t=new Q,r=new Q){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=t,this.v2=r}getPoint(e,t=new Q){const r=t,o=this.v0,l=this.v1,u=this.v2;return r.set($o(e,o.x,l.x,u.x),$o(e,o.y,l.y,u.y),$o(e,o.z,l.z,u.z)),r}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class ag extends bi{constructor(e=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=e}getPoint(e,t=new Ge){const r=t,o=this.points,l=(o.length-1)*e,u=Math.floor(l),f=l-u,d=o[u===0?u:u-1],p=o[u],v=o[u>o.length-2?o.length-1:u+1],g=o[u>o.length-3?o.length-1:u+2];return r.set(Hm(f,d.x,p.x,v.x,g.x),Hm(f,d.y,p.y,v.y,g.y)),r}copy(e){super.copy(e),this.points=[];for(let t=0,r=e.points.length;t<r;t++){const o=e.points[t];this.points.push(o.clone())}return this}toJSON(){const e=super.toJSON();e.points=[];for(let t=0,r=this.points.length;t<r;t++){const o=this.points[t];e.points.push(o.toArray())}return e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,r=e.points.length;t<r;t++){const o=e.points[t];this.points.push(new Ge().fromArray(o))}return this}}var ud=Object.freeze({__proto__:null,ArcCurve:fy,CatmullRomCurve3:dy,CubicBezierCurve:rg,CubicBezierCurve3:yy,EllipseCurve:bd,LineCurve:sg,LineCurve3:Sy,QuadraticBezierCurve:og,QuadraticBezierCurve3:My,SplineCurve:ag});class Ey extends bi{constructor(){super(),this.type="CurvePath",this.curves=[],this.autoClose=!1}add(e){this.curves.push(e)}closePath(){const e=this.curves[0].getPoint(0),t=this.curves[this.curves.length-1].getPoint(1);if(!e.equals(t)){const r=e.isVector2===!0?"LineCurve":"LineCurve3";this.curves.push(new ud[r](t,e))}return this}getPoint(e,t){const r=e*this.getLength(),o=this.getCurveLengths();let l=0;for(;l<o.length;){if(o[l]>=r){const u=o[l]-r,f=this.curves[l],d=f.getLength(),p=d===0?0:1-u/d;return f.getPointAt(p,t)}l++}return null}getLength(){const e=this.getCurveLengths();return e[e.length-1]}updateArcLengths(){this.needsUpdate=!0,this.cacheLengths=null,this.getCurveLengths()}getCurveLengths(){if(this.cacheLengths&&this.cacheLengths.length===this.curves.length)return this.cacheLengths;const e=[];let t=0;for(let r=0,o=this.curves.length;r<o;r++)t+=this.curves[r].getLength(),e.push(t);return this.cacheLengths=e,e}getSpacedPoints(e=40){const t=[];for(let r=0;r<=e;r++)t.push(this.getPoint(r/e));return this.autoClose&&t.push(t[0]),t}getPoints(e=12){const t=[];let r;for(let o=0,l=this.curves;o<l.length;o++){const u=l[o],f=u.isEllipseCurve?e*2:u.isLineCurve||u.isLineCurve3?1:u.isSplineCurve?e*u.points.length:e,d=u.getPoints(f);for(let p=0;p<d.length;p++){const v=d[p];r&&r.equals(v)||(t.push(v),r=v)}}return this.autoClose&&t.length>1&&!t[t.length-1].equals(t[0])&&t.push(t[0]),t}copy(e){super.copy(e),this.curves=[];for(let t=0,r=e.curves.length;t<r;t++){const o=e.curves[t];this.curves.push(o.clone())}return this.autoClose=e.autoClose,this}toJSON(){const e=super.toJSON();e.autoClose=this.autoClose,e.curves=[];for(let t=0,r=this.curves.length;t<r;t++){const o=this.curves[t];e.curves.push(o.toJSON())}return e}fromJSON(e){super.fromJSON(e),this.autoClose=e.autoClose,this.curves=[];for(let t=0,r=e.curves.length;t<r;t++){const o=e.curves[t];this.curves.push(new ud[o.type]().fromJSON(o))}return this}}class Vm extends Ey{constructor(e){super(),this.type="Path",this.currentPoint=new Ge,e&&this.setFromPoints(e)}setFromPoints(e){this.moveTo(e[0].x,e[0].y);for(let t=1,r=e.length;t<r;t++)this.lineTo(e[t].x,e[t].y);return this}moveTo(e,t){return this.currentPoint.set(e,t),this}lineTo(e,t){const r=new sg(this.currentPoint.clone(),new Ge(e,t));return this.curves.push(r),this.currentPoint.set(e,t),this}quadraticCurveTo(e,t,r,o){const l=new og(this.currentPoint.clone(),new Ge(e,t),new Ge(r,o));return this.curves.push(l),this.currentPoint.set(r,o),this}bezierCurveTo(e,t,r,o,l,u){const f=new rg(this.currentPoint.clone(),new Ge(e,t),new Ge(r,o),new Ge(l,u));return this.curves.push(f),this.currentPoint.set(l,u),this}splineThru(e){const t=[this.currentPoint.clone()].concat(e),r=new ag(t);return this.curves.push(r),this.currentPoint.copy(e[e.length-1]),this}arc(e,t,r,o,l,u){const f=this.currentPoint.x,d=this.currentPoint.y;return this.absarc(e+f,t+d,r,o,l,u),this}absarc(e,t,r,o,l,u){return this.absellipse(e,t,r,r,o,l,u),this}ellipse(e,t,r,o,l,u,f,d){const p=this.currentPoint.x,v=this.currentPoint.y;return this.absellipse(e+p,t+v,r,o,l,u,f,d),this}absellipse(e,t,r,o,l,u,f,d){const p=new bd(e,t,r,o,l,u,f,d);if(this.curves.length>0){const g=p.getPoint(0);g.equals(this.currentPoint)||this.lineTo(g.x,g.y)}this.curves.push(p);const v=p.getPoint(1);return this.currentPoint.copy(v),this}copy(e){return super.copy(e),this.currentPoint.copy(e.currentPoint),this}toJSON(){const e=super.toJSON();return e.currentPoint=this.currentPoint.toArray(),e}fromJSON(e){return super.fromJSON(e),this.currentPoint.fromArray(e.currentPoint),this}}class Ld extends Vm{constructor(e){super(e),this.uuid=oo(),this.type="Shape",this.holes=[]}getPointsHoles(e){const t=[];for(let r=0,o=this.holes.length;r<o;r++)t[r]=this.holes[r].getPoints(e);return t}extractPoints(e){return{shape:this.getPoints(e),holes:this.getPointsHoles(e)}}copy(e){super.copy(e),this.holes=[];for(let t=0,r=e.holes.length;t<r;t++){const o=e.holes[t];this.holes.push(o.clone())}return this}toJSON(){const e=super.toJSON();e.uuid=this.uuid,e.holes=[];for(let t=0,r=this.holes.length;t<r;t++){const o=this.holes[t];e.holes.push(o.toJSON())}return e}fromJSON(e){super.fromJSON(e),this.uuid=e.uuid,this.holes=[];for(let t=0,r=e.holes.length;t<r;t++){const o=e.holes[t];this.holes.push(new Vm().fromJSON(o))}return this}}function wy(s,e,t=2){const r=e&&e.length,o=r?e[0]*t:s.length;let l=lg(s,0,o,t,!0);const u=[];if(!l||l.next===l.prev)return u;let f,d,p;if(r&&(l=by(s,e,l,t)),s.length>80*t){f=1/0,d=1/0;let v=-1/0,g=-1/0;for(let _=t;_<o;_+=t){const S=s[_],M=s[_+1];S<f&&(f=S),M<d&&(d=M),S>v&&(v=S),M>g&&(g=M)}p=Math.max(v-f,g-d),p=p!==0?32767/p:0}return ia(l,u,t,f,d,p,0),u}function lg(s,e,t,r,o){let l;if(o===zy(s,e,t,r)>0)for(let u=e;u<t;u+=r)l=Gm(u/r|0,s[u],s[u+1],l);else for(let u=t-r;u>=e;u-=r)l=Gm(u/r|0,s[u],s[u+1],l);return l&&io(l,l.next)&&(sa(l),l=l.next),l}function as(s,e){if(!s)return s;e||(e=s);let t=s,r;do if(r=!1,!t.steiner&&(io(t,t.next)||Yt(t.prev,t,t.next)===0)){if(sa(t),t=e=t.prev,t===t.next)break;r=!0}else t=t.next;while(r||t!==e);return e}function ia(s,e,t,r,o,l,u){if(!s)return;!u&&l&&Iy(s,r,o,l);let f=s;for(;s.prev!==s.next;){const d=s.prev,p=s.next;if(l?Ay(s,r,o,l):Ty(s)){e.push(d.i,s.i,p.i),sa(s),s=p.next,f=p.next;continue}if(s=p,s===f){u?u===1?(s=Ry(as(s),e),ia(s,e,t,r,o,l,2)):u===2&&Cy(s,e,t,r,o,l):ia(as(s),e,t,r,o,l,1);break}}}function Ty(s){const e=s.prev,t=s,r=s.next;if(Yt(e,t,r)>=0)return!1;const o=e.x,l=t.x,u=r.x,f=e.y,d=t.y,p=r.y,v=Math.min(o,l,u),g=Math.min(f,d,p),_=Math.max(o,l,u),S=Math.max(f,d,p);let M=r.next;for(;M!==e;){if(M.x>=v&&M.x<=_&&M.y>=g&&M.y<=S&&qo(o,f,l,d,u,p,M.x,M.y)&&Yt(M.prev,M,M.next)>=0)return!1;M=M.next}return!0}function Ay(s,e,t,r){const o=s.prev,l=s,u=s.next;if(Yt(o,l,u)>=0)return!1;const f=o.x,d=l.x,p=u.x,v=o.y,g=l.y,_=u.y,S=Math.min(f,d,p),M=Math.min(v,g,_),A=Math.max(f,d,p),y=Math.max(v,g,_),x=fd(S,M,e,t,r),O=fd(A,y,e,t,r);let D=s.prevZ,R=s.nextZ;for(;D&&D.z>=x&&R&&R.z<=O;){if(D.x>=S&&D.x<=A&&D.y>=M&&D.y<=y&&D!==o&&D!==u&&qo(f,v,d,g,p,_,D.x,D.y)&&Yt(D.prev,D,D.next)>=0||(D=D.prevZ,R.x>=S&&R.x<=A&&R.y>=M&&R.y<=y&&R!==o&&R!==u&&qo(f,v,d,g,p,_,R.x,R.y)&&Yt(R.prev,R,R.next)>=0))return!1;R=R.nextZ}for(;D&&D.z>=x;){if(D.x>=S&&D.x<=A&&D.y>=M&&D.y<=y&&D!==o&&D!==u&&qo(f,v,d,g,p,_,D.x,D.y)&&Yt(D.prev,D,D.next)>=0)return!1;D=D.prevZ}for(;R&&R.z<=O;){if(R.x>=S&&R.x<=A&&R.y>=M&&R.y<=y&&R!==o&&R!==u&&qo(f,v,d,g,p,_,R.x,R.y)&&Yt(R.prev,R,R.next)>=0)return!1;R=R.nextZ}return!0}function Ry(s,e){let t=s;do{const r=t.prev,o=t.next.next;!io(r,o)&&ug(r,t,t.next,o)&&ra(r,o)&&ra(o,r)&&(e.push(r.i,t.i,o.i),sa(t),sa(t.next),t=s=o),t=t.next}while(t!==s);return as(t)}function Cy(s,e,t,r,o,l){let u=s;do{let f=u.next.next;for(;f!==u.prev;){if(u.i!==f.i&&Oy(u,f)){let d=fg(u,f);u=as(u,u.next),d=as(d,d.next),ia(u,e,t,r,o,l,0),ia(d,e,t,r,o,l,0);return}f=f.next}u=u.next}while(u!==s)}function by(s,e,t,r){const o=[];for(let l=0,u=e.length;l<u;l++){const f=e[l]*r,d=l<u-1?e[l+1]*r:s.length,p=lg(s,f,d,r,!1);p===p.next&&(p.steiner=!0),o.push(Fy(p))}o.sort(Py);for(let l=0;l<o.length;l++)t=Ly(o[l],t);return t}function Py(s,e){let t=s.x-e.x;if(t===0&&(t=s.y-e.y,t===0)){const r=(s.next.y-s.y)/(s.next.x-s.x),o=(e.next.y-e.y)/(e.next.x-e.x);t=r-o}return t}function Ly(s,e){const t=Dy(s,e);if(!t)return e;const r=fg(t,s);return as(r,r.next),as(t,t.next)}function Dy(s,e){let t=e;const r=s.x,o=s.y;let l=-1/0,u;if(io(s,t))return t;do{if(io(s,t.next))return t.next;if(o<=t.y&&o>=t.next.y&&t.next.y!==t.y){const g=t.x+(o-t.y)*(t.next.x-t.x)/(t.next.y-t.y);if(g<=r&&g>l&&(l=g,u=t.x<t.next.x?t:t.next,g===r))return u}t=t.next}while(t!==e);if(!u)return null;const f=u,d=u.x,p=u.y;let v=1/0;t=u;do{if(r>=t.x&&t.x>=d&&r!==t.x&&cg(o<p?r:l,o,d,p,o<p?l:r,o,t.x,t.y)){const g=Math.abs(o-t.y)/(r-t.x);ra(t,s)&&(g<v||g===v&&(t.x>u.x||t.x===u.x&&Ny(u,t)))&&(u=t,v=g)}t=t.next}while(t!==f);return u}function Ny(s,e){return Yt(s.prev,s,e.prev)<0&&Yt(e.next,s,s.next)<0}function Iy(s,e,t,r){let o=s;do o.z===0&&(o.z=fd(o.x,o.y,e,t,r)),o.prevZ=o.prev,o.nextZ=o.next,o=o.next;while(o!==s);o.prevZ.nextZ=null,o.prevZ=null,Uy(o)}function Uy(s){let e,t=1;do{let r=s,o;s=null;let l=null;for(e=0;r;){e++;let u=r,f=0;for(let p=0;p<t&&(f++,u=u.nextZ,!!u);p++);let d=t;for(;f>0||d>0&&u;)f!==0&&(d===0||!u||r.z<=u.z)?(o=r,r=r.nextZ,f--):(o=u,u=u.nextZ,d--),l?l.nextZ=o:s=o,o.prevZ=l,l=o;r=u}l.nextZ=null,t*=2}while(e>1);return s}function fd(s,e,t,r,o){return s=(s-t)*o|0,e=(e-r)*o|0,s=(s|s<<8)&16711935,s=(s|s<<4)&252645135,s=(s|s<<2)&858993459,s=(s|s<<1)&1431655765,e=(e|e<<8)&16711935,e=(e|e<<4)&252645135,e=(e|e<<2)&858993459,e=(e|e<<1)&1431655765,s|e<<1}function Fy(s){let e=s,t=s;do(e.x<t.x||e.x===t.x&&e.y<t.y)&&(t=e),e=e.next;while(e!==s);return t}function cg(s,e,t,r,o,l,u,f){return(o-u)*(e-f)>=(s-u)*(l-f)&&(s-u)*(r-f)>=(t-u)*(e-f)&&(t-u)*(l-f)>=(o-u)*(r-f)}function qo(s,e,t,r,o,l,u,f){return!(s===u&&e===f)&&cg(s,e,t,r,o,l,u,f)}function Oy(s,e){return s.next.i!==e.i&&s.prev.i!==e.i&&!ky(s,e)&&(ra(s,e)&&ra(e,s)&&By(s,e)&&(Yt(s.prev,s,e.prev)||Yt(s,e.prev,e))||io(s,e)&&Yt(s.prev,s,s.next)>0&&Yt(e.prev,e,e.next)>0)}function Yt(s,e,t){return(e.y-s.y)*(t.x-e.x)-(e.x-s.x)*(t.y-e.y)}function io(s,e){return s.x===e.x&&s.y===e.y}function ug(s,e,t,r){const o=Il(Yt(s,e,t)),l=Il(Yt(s,e,r)),u=Il(Yt(t,r,s)),f=Il(Yt(t,r,e));return!!(o!==l&&u!==f||o===0&&Nl(s,t,e)||l===0&&Nl(s,r,e)||u===0&&Nl(t,s,r)||f===0&&Nl(t,e,r))}function Nl(s,e,t){return e.x<=Math.max(s.x,t.x)&&e.x>=Math.min(s.x,t.x)&&e.y<=Math.max(s.y,t.y)&&e.y>=Math.min(s.y,t.y)}function Il(s){return s>0?1:s<0?-1:0}function ky(s,e){let t=s;do{if(t.i!==s.i&&t.next.i!==s.i&&t.i!==e.i&&t.next.i!==e.i&&ug(t,t.next,s,e))return!0;t=t.next}while(t!==s);return!1}function ra(s,e){return Yt(s.prev,s,s.next)<0?Yt(s,e,s.next)>=0&&Yt(s,s.prev,e)>=0:Yt(s,e,s.prev)<0||Yt(s,s.next,e)<0}function By(s,e){let t=s,r=!1;const o=(s.x+e.x)/2,l=(s.y+e.y)/2;do t.y>l!=t.next.y>l&&t.next.y!==t.y&&o<(t.next.x-t.x)*(l-t.y)/(t.next.y-t.y)+t.x&&(r=!r),t=t.next;while(t!==s);return r}function fg(s,e){const t=dd(s.i,s.x,s.y),r=dd(e.i,e.x,e.y),o=s.next,l=e.prev;return s.next=e,e.prev=s,t.next=o,o.prev=t,r.next=t,t.prev=r,l.next=r,r.prev=l,r}function Gm(s,e,t,r){const o=dd(s,e,t);return r?(o.next=r.next,o.prev=r,r.next.prev=o,r.next=o):(o.prev=o,o.next=o),o}function sa(s){s.next.prev=s.prev,s.prev.next=s.next,s.prevZ&&(s.prevZ.nextZ=s.nextZ),s.nextZ&&(s.nextZ.prevZ=s.prevZ)}function dd(s,e,t){return{i:s,x:e,y:t,prev:null,next:null,z:0,prevZ:null,nextZ:null,steiner:!1}}function zy(s,e,t,r){let o=0;for(let l=e,u=t-r;l<t;l+=r)o+=(s[u]-s[l])*(s[l+1]+s[u+1]),u=l;return o}class Hy{static triangulate(e,t,r=2){return wy(e,t,r)}}class qi{static area(e){const t=e.length;let r=0;for(let o=t-1,l=0;l<t;o=l++)r+=e[o].x*e[l].y-e[l].x*e[o].y;return r*.5}static isClockWise(e){return qi.area(e)<0}static triangulateShape(e,t){const r=[],o=[],l=[];Wm(e),Xm(r,e);let u=e.length;t.forEach(Wm);for(let d=0;d<t.length;d++)o.push(u),u+=t[d].length,Xm(r,t[d]);const f=Hy.triangulate(r,o);for(let d=0;d<f.length;d+=3)l.push(f.slice(d,d+3));return l}}function Wm(s){const e=s.length;e>2&&s[e-1].equals(s[0])&&s.pop()}function Xm(s,e){for(let t=0;t<e.length;t++)s.push(e[t].x),s.push(e[t].y)}class Dd extends Ci{constructor(e=new Ld([new Ge(.5,.5),new Ge(-.5,.5),new Ge(-.5,-.5),new Ge(.5,-.5)]),t={}){super(),this.type="ExtrudeGeometry",this.parameters={shapes:e,options:t},e=Array.isArray(e)?e:[e];const r=this,o=[],l=[];for(let f=0,d=e.length;f<d;f++){const p=e[f];u(p)}this.setAttribute("position",new In(o,3)),this.setAttribute("uv",new In(l,2)),this.computeVertexNormals();function u(f){const d=[],p=t.curveSegments!==void 0?t.curveSegments:12,v=t.steps!==void 0?t.steps:1,g=t.depth!==void 0?t.depth:1;let _=t.bevelEnabled!==void 0?t.bevelEnabled:!0,S=t.bevelThickness!==void 0?t.bevelThickness:.2,M=t.bevelSize!==void 0?t.bevelSize:S-.1,A=t.bevelOffset!==void 0?t.bevelOffset:0,y=t.bevelSegments!==void 0?t.bevelSegments:3;const x=t.extrudePath,O=t.UVGenerator!==void 0?t.UVGenerator:Vy;let D,R=!1,z,H,I,N;x&&(D=x.getSpacedPoints(v),R=!0,_=!1,z=x.computeFrenetFrames(v,!1),H=new Q,I=new Q,N=new Q),_||(y=0,S=0,M=0,A=0);const C=f.extractPoints(p);let T=C.shape;const F=C.holes;if(!qi.isClockWise(T)){T=T.reverse();for(let Me=0,_e=F.length;Me<_e;Me++){const Se=F[Me];qi.isClockWise(Se)&&(F[Me]=Se.reverse())}}function ee(Me){const Se=10000000000000001e-36;let fe=Me[0];for(let be=1;be<=Me.length;be++){const xe=be%Me.length,Re=Me[xe],ct=Re.x-fe.x,ft=Re.y-fe.y,L=ct*ct+ft*ft,w=Math.max(Math.abs(Re.x),Math.abs(Re.y),Math.abs(fe.x),Math.abs(fe.y)),J=Se*w*w;if(L<=J){Me.splice(xe,1),be--;continue}fe=Re}}ee(T),F.forEach(ee);const le=F.length,ne=T;for(let Me=0;Me<le;Me++){const _e=F[Me];T=T.concat(_e)}function ce(Me,_e,Se){return _e||console.error("THREE.ExtrudeGeometry: vec does not exist"),Me.clone().addScaledVector(_e,Se)}const re=T.length;function V(Me,_e,Se){let fe,be,xe;const Re=Me.x-_e.x,ct=Me.y-_e.y,ft=Se.x-Me.x,L=Se.y-Me.y,w=Re*Re+ct*ct,J=Re*L-ct*ft;if(Math.abs(J)>Number.EPSILON){const ge=Math.sqrt(w),Ae=Math.sqrt(ft*ft+L*L),ve=_e.x-ct/ge,Je=_e.y+Re/ge,Le=Se.x-L/Ae,Ke=Se.y+ft/Ae,nt=((Le-ve)*L-(Ke-Je)*ft)/(Re*L-ct*ft);fe=ve+Re*nt-Me.x,be=Je+ct*nt-Me.y;const Ie=fe*fe+be*be;if(Ie<=2)return new Ge(fe,be);xe=Math.sqrt(Ie/2)}else{let ge=!1;Re>Number.EPSILON?ft>Number.EPSILON&&(ge=!0):Re<-Number.EPSILON?ft<-Number.EPSILON&&(ge=!0):Math.sign(ct)===Math.sign(L)&&(ge=!0),ge?(fe=-ct,be=Re,xe=Math.sqrt(w)):(fe=Re,be=ct,xe=Math.sqrt(w/2))}return new Ge(fe/xe,be/xe)}const me=[];for(let Me=0,_e=ne.length,Se=_e-1,fe=Me+1;Me<_e;Me++,Se++,fe++)Se===_e&&(Se=0),fe===_e&&(fe=0),me[Me]=V(ne[Me],ne[Se],ne[fe]);const ie=[];let P,B=me.concat();for(let Me=0,_e=le;Me<_e;Me++){const Se=F[Me];P=[];for(let fe=0,be=Se.length,xe=be-1,Re=fe+1;fe<be;fe++,xe++,Re++)xe===be&&(xe=0),Re===be&&(Re=0),P[fe]=V(Se[fe],Se[xe],Se[Re]);ie.push(P),B=B.concat(P)}let Z;if(y===0)Z=qi.triangulateShape(ne,F);else{const Me=[],_e=[];for(let Se=0;Se<y;Se++){const fe=Se/y,be=S*Math.cos(fe*Math.PI/2),xe=M*Math.sin(fe*Math.PI/2)+A;for(let Re=0,ct=ne.length;Re<ct;Re++){const ft=ce(ne[Re],me[Re],xe);ye(ft.x,ft.y,-be),fe===0&&Me.push(ft)}for(let Re=0,ct=le;Re<ct;Re++){const ft=F[Re];P=ie[Re];const L=[];for(let w=0,J=ft.length;w<J;w++){const ge=ce(ft[w],P[w],xe);ye(ge.x,ge.y,-be),fe===0&&L.push(ge)}fe===0&&_e.push(L)}}Z=qi.triangulateShape(Me,_e)}const ue=Z.length,he=M+A;for(let Me=0;Me<re;Me++){const _e=_?ce(T[Me],B[Me],he):T[Me];R?(I.copy(z.normals[0]).multiplyScalar(_e.x),H.copy(z.binormals[0]).multiplyScalar(_e.y),N.copy(D[0]).add(I).add(H),ye(N.x,N.y,N.z)):ye(_e.x,_e.y,0)}for(let Me=1;Me<=v;Me++)for(let _e=0;_e<re;_e++){const Se=_?ce(T[_e],B[_e],he):T[_e];R?(I.copy(z.normals[Me]).multiplyScalar(Se.x),H.copy(z.binormals[Me]).multiplyScalar(Se.y),N.copy(D[Me]).add(I).add(H),ye(N.x,N.y,N.z)):ye(Se.x,Se.y,g/v*Me)}for(let Me=y-1;Me>=0;Me--){const _e=Me/y,Se=S*Math.cos(_e*Math.PI/2),fe=M*Math.sin(_e*Math.PI/2)+A;for(let be=0,xe=ne.length;be<xe;be++){const Re=ce(ne[be],me[be],fe);ye(Re.x,Re.y,g+Se)}for(let be=0,xe=F.length;be<xe;be++){const Re=F[be];P=ie[be];for(let ct=0,ft=Re.length;ct<ft;ct++){const L=ce(Re[ct],P[ct],fe);R?ye(L.x,L.y+D[v-1].y,D[v-1].x+Se):ye(L.x,L.y,g+Se)}}}K(),oe();function K(){const Me=o.length/3;if(_){let _e=0,Se=re*_e;for(let fe=0;fe<ue;fe++){const be=Z[fe];we(be[2]+Se,be[1]+Se,be[0]+Se)}_e=v+y*2,Se=re*_e;for(let fe=0;fe<ue;fe++){const be=Z[fe];we(be[0]+Se,be[1]+Se,be[2]+Se)}}else{for(let _e=0;_e<ue;_e++){const Se=Z[_e];we(Se[2],Se[1],Se[0])}for(let _e=0;_e<ue;_e++){const Se=Z[_e];we(Se[0]+re*v,Se[1]+re*v,Se[2]+re*v)}}r.addGroup(Me,o.length/3-Me,0)}function oe(){const Me=o.length/3;let _e=0;Ee(ne,_e),_e+=ne.length;for(let Se=0,fe=F.length;Se<fe;Se++){const be=F[Se];Ee(be,_e),_e+=be.length}r.addGroup(Me,o.length/3-Me,1)}function Ee(Me,_e){let Se=Me.length;for(;--Se>=0;){const fe=Se;let be=Se-1;be<0&&(be=Me.length-1);for(let xe=0,Re=v+y*2;xe<Re;xe++){const ct=re*xe,ft=re*(xe+1),L=_e+fe+ct,w=_e+be+ct,J=_e+be+ft,ge=_e+fe+ft;tt(L,w,J,ge)}}}function ye(Me,_e,Se){d.push(Me),d.push(_e),d.push(Se)}function we(Me,_e,Se){at(Me),at(_e),at(Se);const fe=o.length/3,be=O.generateTopUV(r,o,fe-3,fe-2,fe-1);U(be[0]),U(be[1]),U(be[2])}function tt(Me,_e,Se,fe){at(Me),at(_e),at(fe),at(_e),at(Se),at(fe);const be=o.length/3,xe=O.generateSideWallUV(r,o,be-6,be-3,be-2,be-1);U(xe[0]),U(xe[1]),U(xe[3]),U(xe[1]),U(xe[2]),U(xe[3])}function at(Me){o.push(d[Me*3+0]),o.push(d[Me*3+1]),o.push(d[Me*3+2])}function U(Me){l.push(Me.x),l.push(Me.y)}}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){const e=super.toJSON(),t=this.parameters.shapes,r=this.parameters.options;return Gy(t,r,e)}static fromJSON(e,t){const r=[];for(let l=0,u=e.shapes.length;l<u;l++){const f=t[e.shapes[l]];r.push(f)}const o=e.options.extrudePath;return o!==void 0&&(e.options.extrudePath=new ud[o.type]().fromJSON(o)),new Dd(r,e.options)}}const Vy={generateTopUV:function(s,e,t,r,o){const l=e[t*3],u=e[t*3+1],f=e[r*3],d=e[r*3+1],p=e[o*3],v=e[o*3+1];return[new Ge(l,u),new Ge(f,d),new Ge(p,v)]},generateSideWallUV:function(s,e,t,r,o,l){const u=e[t*3],f=e[t*3+1],d=e[t*3+2],p=e[r*3],v=e[r*3+1],g=e[r*3+2],_=e[o*3],S=e[o*3+1],M=e[o*3+2],A=e[l*3],y=e[l*3+1],x=e[l*3+2];return Math.abs(f-v)<Math.abs(u-p)?[new Ge(u,1-d),new Ge(p,1-g),new Ge(_,1-M),new Ge(A,1-x)]:[new Ge(f,1-d),new Ge(v,1-g),new Ge(S,1-M),new Ge(y,1-x)]}};function Gy(s,e,t){if(t.shapes=[],Array.isArray(s))for(let r=0,o=s.length;r<o;r++){const l=s[r];t.shapes.push(l.uuid)}else t.shapes.push(s.uuid);return t.options=Object.assign({},e),e.extrudePath!==void 0&&(t.options.extrudePath=e.extrudePath.toJSON()),t}class ua extends Ci{constructor(e=1,t=1,r=1,o=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:r,heightSegments:o};const l=e/2,u=t/2,f=Math.floor(r),d=Math.floor(o),p=f+1,v=d+1,g=e/f,_=t/d,S=[],M=[],A=[],y=[];for(let x=0;x<v;x++){const O=x*_-u;for(let D=0;D<p;D++){const R=D*g-l;M.push(R,-O,0),A.push(0,0,1),y.push(D/f),y.push(1-x/d)}}for(let x=0;x<d;x++)for(let O=0;O<f;O++){const D=O+p*x,R=O+p*(x+1),z=O+1+p*(x+1),H=O+1+p*x;S.push(D,R,H),S.push(R,z,H)}this.setIndex(S),this.setAttribute("position",new In(M,3)),this.setAttribute("normal",new In(A,3)),this.setAttribute("uv",new In(y,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ua(e.width,e.height,e.widthSegments,e.heightSegments)}}class Nd extends Ci{constructor(e=new Ld([new Ge(0,.5),new Ge(-.5,-.5),new Ge(.5,-.5)]),t=12){super(),this.type="ShapeGeometry",this.parameters={shapes:e,curveSegments:t};const r=[],o=[],l=[],u=[];let f=0,d=0;if(Array.isArray(e)===!1)p(e);else for(let v=0;v<e.length;v++)p(e[v]),this.addGroup(f,d,v),f+=d,d=0;this.setIndex(r),this.setAttribute("position",new In(o,3)),this.setAttribute("normal",new In(l,3)),this.setAttribute("uv",new In(u,2));function p(v){const g=o.length/3,_=v.extractPoints(t);let S=_.shape;const M=_.holes;qi.isClockWise(S)===!1&&(S=S.reverse());for(let y=0,x=M.length;y<x;y++){const O=M[y];qi.isClockWise(O)===!0&&(M[y]=O.reverse())}const A=qi.triangulateShape(S,M);for(let y=0,x=M.length;y<x;y++){const O=M[y];S=S.concat(O)}for(let y=0,x=S.length;y<x;y++){const O=S[y];o.push(O.x,O.y,0),l.push(0,0,1),u.push(O.x,O.y)}for(let y=0,x=A.length;y<x;y++){const O=A[y],D=O[0]+g,R=O[1]+g,z=O[2]+g;r.push(D,R,z),d+=3}}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){const e=super.toJSON(),t=this.parameters.shapes;return Wy(t,e)}static fromJSON(e,t){const r=[];for(let o=0,l=e.shapes.length;o<l;o++){const u=t[e.shapes[o]];r.push(u)}return new Nd(r,e.curveSegments)}}function Wy(s,e){if(e.shapes=[],Array.isArray(s))for(let t=0,r=s.length;t<r;t++){const o=s[t];e.shapes.push(o.uuid)}else e.shapes.push(s.uuid);return e}class Ul extends ca{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new It(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new It(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=X0,this.normalScale=new Ge(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Ri,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}}class Xy extends ca{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Ex,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class jy extends ca{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}class dg extends _n{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new It(e),this.intensity=t}dispose(){}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){const t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,this.groundColor!==void 0&&(t.object.groundColor=this.groundColor.getHex()),this.distance!==void 0&&(t.object.distance=this.distance),this.angle!==void 0&&(t.object.angle=this.angle),this.decay!==void 0&&(t.object.decay=this.decay),this.penumbra!==void 0&&(t.object.penumbra=this.penumbra),this.shadow!==void 0&&(t.object.shadow=this.shadow.toJSON()),this.target!==void 0&&(t.object.target=this.target.uuid),t}}class qy extends dg{constructor(e,t,r){super(e,r),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(_n.DEFAULT_UP),this.updateMatrix(),this.groundColor=new It(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}}const mf=new $t,jm=new Q,qm=new Q;class Yy{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new Ge(512,512),this.mapType=Ai,this.map=null,this.mapPass=null,this.matrix=new $t,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new Cd,this._frameExtents=new Ge(1,1),this._viewportCount=1,this._viewports=[new Zt(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(e){const t=this.camera,r=this.matrix;jm.setFromMatrixPosition(e.matrixWorld),t.position.copy(jm),qm.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(qm),t.updateMatrixWorld(),mf.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),this._frustum.setFromProjectionMatrix(mf,t.coordinateSystem,t.reversedDepth),t.reversedDepth?r.set(.5,0,0,.5,0,.5,0,.5,0,0,1,0,0,0,0,1):r.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),r.multiply(mf)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this}clone(){return new this.constructor().copy(this)}toJSON(){const e={};return this.intensity!==1&&(e.intensity=this.intensity),this.bias!==0&&(e.bias=this.bias),this.normalBias!==0&&(e.normalBias=this.normalBias),this.radius!==1&&(e.radius=this.radius),(this.mapSize.x!==512||this.mapSize.y!==512)&&(e.mapSize=this.mapSize.toArray()),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}}class hg extends eg{constructor(e=-1,t=1,r=1,o=-1,l=.1,u=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=r,this.bottom=o,this.near=l,this.far=u,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,r,o,l,u){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=r,this.view.offsetY=o,this.view.width=l,this.view.height=u,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),r=(this.right+this.left)/2,o=(this.top+this.bottom)/2;let l=r-e,u=r+e,f=o+t,d=o-t;if(this.view!==null&&this.view.enabled){const p=(this.right-this.left)/this.view.fullWidth/this.zoom,v=(this.top-this.bottom)/this.view.fullHeight/this.zoom;l+=p*this.view.offsetX,u=l+p*this.view.width,f-=v*this.view.offsetY,d=f-v*this.view.height}this.projectionMatrix.makeOrthographic(l,u,f,d,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class $y extends Yy{constructor(){super(new hg(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}}class Ym extends dg{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(_n.DEFAULT_UP),this.updateMatrix(),this.target=new _n,this.shadow=new $y}dispose(){this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}}class Ky extends ri{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}const $m=new $t;class Zy{constructor(e,t,r=0,o=1/0){this.ray=new $0(e,t),this.near=r,this.far=o,this.camera=null,this.layers=new Rd,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,t){this.ray.set(e,t)}setFromCamera(e,t){t.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(t).sub(this.ray.origin).normalize(),this.camera=t):t.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,(t.near+t.far)/(t.near-t.far)).unproject(t),this.ray.direction.set(0,0,-1).transformDirection(t.matrixWorld),this.camera=t):console.error("THREE.Raycaster: Unsupported camera type: "+t.type)}setFromXRController(e){return $m.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4($m),this}intersectObject(e,t=!0,r=[]){return hd(e,this,r,t),r.sort(Km),r}intersectObjects(e,t=!0,r=[]){for(let o=0,l=e.length;o<l;o++)hd(e[o],this,r,t);return r.sort(Km),r}}function Km(s,e){return s.distance-e.distance}function hd(s,e,t,r){let o=!0;if(s.layers.test(e.layers)&&s.raycast(e,t)===!1&&(o=!1),o===!0&&r===!0){const l=s.children;for(let u=0,f=l.length;u<f;u++)hd(l[u],e,t,!0)}}function Zm(s,e,t,r){const o=Jy(r);switch(t){case H0:return s*e;case G0:return s*e/o.components*o.byteLength;case Md:return s*e/o.components*o.byteLength;case W0:return s*e*2/o.components*o.byteLength;case Ed:return s*e*2/o.components*o.byteLength;case V0:return s*e*3/o.components*o.byteLength;case gi:return s*e*4/o.components*o.byteLength;case wd:return s*e*4/o.components*o.byteLength;case Gl:case Wl:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case Xl:case jl:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Ff:case kf:return Math.max(s,16)*Math.max(e,8)/4;case Uf:case Of:return Math.max(s,8)*Math.max(e,8)/2;case Bf:case zf:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case Hf:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Vf:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Gf:return Math.floor((s+4)/5)*Math.floor((e+3)/4)*16;case Wf:return Math.floor((s+4)/5)*Math.floor((e+4)/5)*16;case Xf:return Math.floor((s+5)/6)*Math.floor((e+4)/5)*16;case jf:return Math.floor((s+5)/6)*Math.floor((e+5)/6)*16;case qf:return Math.floor((s+7)/8)*Math.floor((e+4)/5)*16;case Yf:return Math.floor((s+7)/8)*Math.floor((e+5)/6)*16;case $f:return Math.floor((s+7)/8)*Math.floor((e+7)/8)*16;case Kf:return Math.floor((s+9)/10)*Math.floor((e+4)/5)*16;case Zf:return Math.floor((s+9)/10)*Math.floor((e+5)/6)*16;case Jf:return Math.floor((s+9)/10)*Math.floor((e+7)/8)*16;case Qf:return Math.floor((s+9)/10)*Math.floor((e+9)/10)*16;case ed:return Math.floor((s+11)/12)*Math.floor((e+9)/10)*16;case td:return Math.floor((s+11)/12)*Math.floor((e+11)/12)*16;case nd:case id:case rd:return Math.ceil(s/4)*Math.ceil(e/4)*16;case sd:case od:return Math.ceil(s/4)*Math.ceil(e/4)*8;case ad:case ld:return Math.ceil(s/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Jy(s){switch(s){case Ai:case O0:return{byteLength:1,components:1};case Jo:case k0:case oa:return{byteLength:2,components:1};case yd:case Sd:return{byteLength:2,components:4};case ss:case xd:case Xi:return{byteLength:4,components:1};case B0:case z0:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${s}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:_d}}));typeof window<"u"&&(window.__THREE__?console.warn("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=_d);/**
 * @license
 * Copyright 2010-2025 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function pg(){let s=null,e=!1,t=null,r=null;function o(l,u){t(l,u),r=s.requestAnimationFrame(o)}return{start:function(){e!==!0&&t!==null&&(r=s.requestAnimationFrame(o),e=!0)},stop:function(){s.cancelAnimationFrame(r),e=!1},setAnimationLoop:function(l){t=l},setContext:function(l){s=l}}}function Qy(s){const e=new WeakMap;function t(f,d){const p=f.array,v=f.usage,g=p.byteLength,_=s.createBuffer();s.bindBuffer(d,_),s.bufferData(d,p,v),f.onUploadCallback();let S;if(p instanceof Float32Array)S=s.FLOAT;else if(typeof Float16Array<"u"&&p instanceof Float16Array)S=s.HALF_FLOAT;else if(p instanceof Uint16Array)f.isFloat16BufferAttribute?S=s.HALF_FLOAT:S=s.UNSIGNED_SHORT;else if(p instanceof Int16Array)S=s.SHORT;else if(p instanceof Uint32Array)S=s.UNSIGNED_INT;else if(p instanceof Int32Array)S=s.INT;else if(p instanceof Int8Array)S=s.BYTE;else if(p instanceof Uint8Array)S=s.UNSIGNED_BYTE;else if(p instanceof Uint8ClampedArray)S=s.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+p);return{buffer:_,type:S,bytesPerElement:p.BYTES_PER_ELEMENT,version:f.version,size:g}}function r(f,d,p){const v=d.array,g=d.updateRanges;if(s.bindBuffer(p,f),g.length===0)s.bufferSubData(p,0,v);else{g.sort((S,M)=>S.start-M.start);let _=0;for(let S=1;S<g.length;S++){const M=g[_],A=g[S];A.start<=M.start+M.count+1?M.count=Math.max(M.count,A.start+A.count-M.start):(++_,g[_]=A)}g.length=_+1;for(let S=0,M=g.length;S<M;S++){const A=g[S];s.bufferSubData(p,A.start*v.BYTES_PER_ELEMENT,v,A.start,A.count)}d.clearUpdateRanges()}d.onUploadCallback()}function o(f){return f.isInterleavedBufferAttribute&&(f=f.data),e.get(f)}function l(f){f.isInterleavedBufferAttribute&&(f=f.data);const d=e.get(f);d&&(s.deleteBuffer(d.buffer),e.delete(f))}function u(f,d){if(f.isInterleavedBufferAttribute&&(f=f.data),f.isGLBufferAttribute){const v=e.get(f);(!v||v.version<f.version)&&e.set(f,{buffer:f.buffer,type:f.type,bytesPerElement:f.elementSize,version:f.version});return}const p=e.get(f);if(p===void 0)e.set(f,t(f,d));else if(p.version<f.version){if(p.size!==f.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");r(p.buffer,f,d),p.version=f.version}}return{get:o,remove:l,update:u}}var e1=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,t1=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,n1=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,i1=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,r1=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,s1=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,o1=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,a1=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,l1=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,c1=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,u1=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,f1=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,d1=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,h1=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,p1=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,m1=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,g1=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,v1=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,_1=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,x1=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,y1=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,S1=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,M1=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,E1=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,w1=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,T1=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,A1=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,R1=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,C1=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,b1=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,P1="gl_FragColor = linearToOutputTexel( gl_FragColor );",L1=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,D1=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,N1=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,I1=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,U1=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,F1=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,O1=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,k1=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,B1=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,z1=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,H1=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,V1=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,G1=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,W1=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,X1=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,j1=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,q1=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Y1=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,$1=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,K1=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Z1=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,J1=`struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return saturate(v);
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColor;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,Q1=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,eS=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,tS=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,nS=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,iS=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,rS=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,sS=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,oS=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,aS=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,lS=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,cS=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,uS=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,fS=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,dS=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,hS=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,pS=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,mS=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,gS=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,vS=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,_S=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,xS=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,yS=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,SS=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,MS=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,ES=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,wS=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,TS=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,AS=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,RS=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,CS=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,bS=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,PS=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,LS=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,DS=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,NS=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,IS=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,US=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		float depth = unpackRGBAToDepth( texture2D( depths, uv ) );
		#ifdef USE_REVERSED_DEPTH_BUFFER
			return step( depth, compare );
		#else
			return step( compare, depth );
		#endif
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow( sampler2D shadow, vec2 uv, float compare ) {
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		#ifdef USE_REVERSED_DEPTH_BUFFER
			float hard_shadow = step( distribution.x, compare );
		#else
			float hard_shadow = step( compare, distribution.x );
		#endif
		if ( hard_shadow != 1.0 ) {
			float distance = compare - distribution.x;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
		bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		
		float lightToPositionLength = length( lightToPosition );
		if ( lightToPositionLength - shadowCameraFar <= 0.0 && lightToPositionLength - shadowCameraNear >= 0.0 ) {
			float dp = ( lightToPositionLength - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
			#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
				vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
				shadow = (
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
				) * ( 1.0 / 9.0 );
			#else
				shadow = texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
#endif`,FS=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,OS=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,kS=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,BS=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,zS=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,HS=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,VS=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,GS=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,WS=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,XS=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,jS=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,qS=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,YS=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,$S=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,KS=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,ZS=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,JS=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const QS=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,eM=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,tM=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,nM=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,iM=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,rM=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,sM=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,oM=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,aM=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,lM=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`,cM=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,uM=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,fM=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,dM=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,hM=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,pM=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,mM=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,gM=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,vM=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,_M=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,xM=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,yM=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,SM=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,MM=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,EM=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,wM=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecularDirect + sheenSpecularIndirect;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,TM=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,AM=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,RM=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,CM=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,bM=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,PM=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,LM=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,DM=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,wt={alphahash_fragment:e1,alphahash_pars_fragment:t1,alphamap_fragment:n1,alphamap_pars_fragment:i1,alphatest_fragment:r1,alphatest_pars_fragment:s1,aomap_fragment:o1,aomap_pars_fragment:a1,batching_pars_vertex:l1,batching_vertex:c1,begin_vertex:u1,beginnormal_vertex:f1,bsdfs:d1,iridescence_fragment:h1,bumpmap_pars_fragment:p1,clipping_planes_fragment:m1,clipping_planes_pars_fragment:g1,clipping_planes_pars_vertex:v1,clipping_planes_vertex:_1,color_fragment:x1,color_pars_fragment:y1,color_pars_vertex:S1,color_vertex:M1,common:E1,cube_uv_reflection_fragment:w1,defaultnormal_vertex:T1,displacementmap_pars_vertex:A1,displacementmap_vertex:R1,emissivemap_fragment:C1,emissivemap_pars_fragment:b1,colorspace_fragment:P1,colorspace_pars_fragment:L1,envmap_fragment:D1,envmap_common_pars_fragment:N1,envmap_pars_fragment:I1,envmap_pars_vertex:U1,envmap_physical_pars_fragment:j1,envmap_vertex:F1,fog_vertex:O1,fog_pars_vertex:k1,fog_fragment:B1,fog_pars_fragment:z1,gradientmap_pars_fragment:H1,lightmap_pars_fragment:V1,lights_lambert_fragment:G1,lights_lambert_pars_fragment:W1,lights_pars_begin:X1,lights_toon_fragment:q1,lights_toon_pars_fragment:Y1,lights_phong_fragment:$1,lights_phong_pars_fragment:K1,lights_physical_fragment:Z1,lights_physical_pars_fragment:J1,lights_fragment_begin:Q1,lights_fragment_maps:eS,lights_fragment_end:tS,logdepthbuf_fragment:nS,logdepthbuf_pars_fragment:iS,logdepthbuf_pars_vertex:rS,logdepthbuf_vertex:sS,map_fragment:oS,map_pars_fragment:aS,map_particle_fragment:lS,map_particle_pars_fragment:cS,metalnessmap_fragment:uS,metalnessmap_pars_fragment:fS,morphinstance_vertex:dS,morphcolor_vertex:hS,morphnormal_vertex:pS,morphtarget_pars_vertex:mS,morphtarget_vertex:gS,normal_fragment_begin:vS,normal_fragment_maps:_S,normal_pars_fragment:xS,normal_pars_vertex:yS,normal_vertex:SS,normalmap_pars_fragment:MS,clearcoat_normal_fragment_begin:ES,clearcoat_normal_fragment_maps:wS,clearcoat_pars_fragment:TS,iridescence_pars_fragment:AS,opaque_fragment:RS,packing:CS,premultiplied_alpha_fragment:bS,project_vertex:PS,dithering_fragment:LS,dithering_pars_fragment:DS,roughnessmap_fragment:NS,roughnessmap_pars_fragment:IS,shadowmap_pars_fragment:US,shadowmap_pars_vertex:FS,shadowmap_vertex:OS,shadowmask_pars_fragment:kS,skinbase_vertex:BS,skinning_pars_vertex:zS,skinning_vertex:HS,skinnormal_vertex:VS,specularmap_fragment:GS,specularmap_pars_fragment:WS,tonemapping_fragment:XS,tonemapping_pars_fragment:jS,transmission_fragment:qS,transmission_pars_fragment:YS,uv_pars_fragment:$S,uv_pars_vertex:KS,uv_vertex:ZS,worldpos_vertex:JS,background_vert:QS,background_frag:eM,backgroundCube_vert:tM,backgroundCube_frag:nM,cube_vert:iM,cube_frag:rM,depth_vert:sM,depth_frag:oM,distanceRGBA_vert:aM,distanceRGBA_frag:lM,equirect_vert:cM,equirect_frag:uM,linedashed_vert:fM,linedashed_frag:dM,meshbasic_vert:hM,meshbasic_frag:pM,meshlambert_vert:mM,meshlambert_frag:gM,meshmatcap_vert:vM,meshmatcap_frag:_M,meshnormal_vert:xM,meshnormal_frag:yM,meshphong_vert:SM,meshphong_frag:MM,meshphysical_vert:EM,meshphysical_frag:wM,meshtoon_vert:TM,meshtoon_frag:AM,points_vert:RM,points_frag:CM,shadow_vert:bM,shadow_frag:PM,sprite_vert:LM,sprite_frag:DM},je={common:{diffuse:{value:new It(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Et},alphaMap:{value:null},alphaMapTransform:{value:new Et},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Et}},envmap:{envMap:{value:null},envMapRotation:{value:new Et},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Et}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Et}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Et},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Et},normalScale:{value:new Ge(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Et},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Et}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Et}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Et}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new It(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new It(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Et},alphaTest:{value:0},uvTransform:{value:new Et}},sprite:{diffuse:{value:new It(16777215)},opacity:{value:1},center:{value:new Ge(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Et},alphaMap:{value:null},alphaMapTransform:{value:new Et},alphaTest:{value:0}}},Mi={basic:{uniforms:Dn([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.fog]),vertexShader:wt.meshbasic_vert,fragmentShader:wt.meshbasic_frag},lambert:{uniforms:Dn([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new It(0)}}]),vertexShader:wt.meshlambert_vert,fragmentShader:wt.meshlambert_frag},phong:{uniforms:Dn([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new It(0)},specular:{value:new It(1118481)},shininess:{value:30}}]),vertexShader:wt.meshphong_vert,fragmentShader:wt.meshphong_frag},standard:{uniforms:Dn([je.common,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.roughnessmap,je.metalnessmap,je.fog,je.lights,{emissive:{value:new It(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:wt.meshphysical_vert,fragmentShader:wt.meshphysical_frag},toon:{uniforms:Dn([je.common,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.gradientmap,je.fog,je.lights,{emissive:{value:new It(0)}}]),vertexShader:wt.meshtoon_vert,fragmentShader:wt.meshtoon_frag},matcap:{uniforms:Dn([je.common,je.bumpmap,je.normalmap,je.displacementmap,je.fog,{matcap:{value:null}}]),vertexShader:wt.meshmatcap_vert,fragmentShader:wt.meshmatcap_frag},points:{uniforms:Dn([je.points,je.fog]),vertexShader:wt.points_vert,fragmentShader:wt.points_frag},dashed:{uniforms:Dn([je.common,je.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:wt.linedashed_vert,fragmentShader:wt.linedashed_frag},depth:{uniforms:Dn([je.common,je.displacementmap]),vertexShader:wt.depth_vert,fragmentShader:wt.depth_frag},normal:{uniforms:Dn([je.common,je.bumpmap,je.normalmap,je.displacementmap,{opacity:{value:1}}]),vertexShader:wt.meshnormal_vert,fragmentShader:wt.meshnormal_frag},sprite:{uniforms:Dn([je.sprite,je.fog]),vertexShader:wt.sprite_vert,fragmentShader:wt.sprite_frag},background:{uniforms:{uvTransform:{value:new Et},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:wt.background_vert,fragmentShader:wt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Et}},vertexShader:wt.backgroundCube_vert,fragmentShader:wt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:wt.cube_vert,fragmentShader:wt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:wt.equirect_vert,fragmentShader:wt.equirect_frag},distanceRGBA:{uniforms:Dn([je.common,je.displacementmap,{referencePosition:{value:new Q},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:wt.distanceRGBA_vert,fragmentShader:wt.distanceRGBA_frag},shadow:{uniforms:Dn([je.lights,je.fog,{color:{value:new It(0)},opacity:{value:1}}]),vertexShader:wt.shadow_vert,fragmentShader:wt.shadow_frag}};Mi.physical={uniforms:Dn([Mi.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Et},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Et},clearcoatNormalScale:{value:new Ge(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Et},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Et},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Et},sheen:{value:0},sheenColor:{value:new It(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Et},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Et},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Et},transmissionSamplerSize:{value:new Ge},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Et},attenuationDistance:{value:0},attenuationColor:{value:new It(0)},specularColor:{value:new It(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Et},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Et},anisotropyVector:{value:new Ge},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Et}}]),vertexShader:wt.meshphysical_vert,fragmentShader:wt.meshphysical_frag};const Fl={r:0,b:0,g:0},Kr=new Ri,NM=new $t;function IM(s,e,t,r,o,l,u){const f=new It(0);let d=l===!0?0:1,p,v,g=null,_=0,S=null;function M(D){let R=D.isScene===!0?D.background:null;return R&&R.isTexture&&(R=(D.backgroundBlurriness>0?t:e).get(R)),R}function A(D){let R=!1;const z=M(D);z===null?x(f,d):z&&z.isColor&&(x(z,1),R=!0);const H=s.xr.getEnvironmentBlendMode();H==="additive"?r.buffers.color.setClear(0,0,0,1,u):H==="alpha-blend"&&r.buffers.color.setClear(0,0,0,0,u),(s.autoClear||R)&&(r.buffers.depth.setTest(!0),r.buffers.depth.setMask(!0),r.buffers.color.setMask(!0),s.clear(s.autoClearColor,s.autoClearDepth,s.autoClearStencil))}function y(D,R){const z=M(R);z&&(z.isCubeTexture||z.mapping===nc)?(v===void 0&&(v=new an(new ji(1,1,1),new br({name:"BackgroundCubeMaterial",uniforms:no(Mi.backgroundCube.uniforms),vertexShader:Mi.backgroundCube.vertexShader,fragmentShader:Mi.backgroundCube.fragmentShader,side:Gn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),v.geometry.deleteAttribute("normal"),v.geometry.deleteAttribute("uv"),v.onBeforeRender=function(H,I,N){this.matrixWorld.copyPosition(N.matrixWorld)},Object.defineProperty(v.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),o.update(v)),Kr.copy(R.backgroundRotation),Kr.x*=-1,Kr.y*=-1,Kr.z*=-1,z.isCubeTexture&&z.isRenderTargetTexture===!1&&(Kr.y*=-1,Kr.z*=-1),v.material.uniforms.envMap.value=z,v.material.uniforms.flipEnvMap.value=z.isCubeTexture&&z.isRenderTargetTexture===!1?-1:1,v.material.uniforms.backgroundBlurriness.value=R.backgroundBlurriness,v.material.uniforms.backgroundIntensity.value=R.backgroundIntensity,v.material.uniforms.backgroundRotation.value.setFromMatrix4(NM.makeRotationFromEuler(Kr)),v.material.toneMapped=Nt.getTransfer(z.colorSpace)!==kt,(g!==z||_!==z.version||S!==s.toneMapping)&&(v.material.needsUpdate=!0,g=z,_=z.version,S=s.toneMapping),v.layers.enableAll(),D.unshift(v,v.geometry,v.material,0,0,null)):z&&z.isTexture&&(p===void 0&&(p=new an(new ua(2,2),new br({name:"BackgroundMaterial",uniforms:no(Mi.background.uniforms),vertexShader:Mi.background.vertexShader,fragmentShader:Mi.background.fragmentShader,side:Cr,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),p.geometry.deleteAttribute("normal"),Object.defineProperty(p.material,"map",{get:function(){return this.uniforms.t2D.value}}),o.update(p)),p.material.uniforms.t2D.value=z,p.material.uniforms.backgroundIntensity.value=R.backgroundIntensity,p.material.toneMapped=Nt.getTransfer(z.colorSpace)!==kt,z.matrixAutoUpdate===!0&&z.updateMatrix(),p.material.uniforms.uvTransform.value.copy(z.matrix),(g!==z||_!==z.version||S!==s.toneMapping)&&(p.material.needsUpdate=!0,g=z,_=z.version,S=s.toneMapping),p.layers.enableAll(),D.unshift(p,p.geometry,p.material,0,0,null))}function x(D,R){D.getRGB(Fl,Q0(s)),r.buffers.color.setClear(Fl.r,Fl.g,Fl.b,R,u)}function O(){v!==void 0&&(v.geometry.dispose(),v.material.dispose(),v=void 0),p!==void 0&&(p.geometry.dispose(),p.material.dispose(),p=void 0)}return{getClearColor:function(){return f},setClearColor:function(D,R=1){f.set(D),d=R,x(f,d)},getClearAlpha:function(){return d},setClearAlpha:function(D){d=D,x(f,d)},render:A,addToRenderList:y,dispose:O}}function UM(s,e){const t=s.getParameter(s.MAX_VERTEX_ATTRIBS),r={},o=_(null);let l=o,u=!1;function f(T,F,$,ee,le){let ne=!1;const ce=g(ee,$,F);l!==ce&&(l=ce,p(l.object)),ne=S(T,ee,$,le),ne&&M(T,ee,$,le),le!==null&&e.update(le,s.ELEMENT_ARRAY_BUFFER),(ne||u)&&(u=!1,R(T,F,$,ee),le!==null&&s.bindBuffer(s.ELEMENT_ARRAY_BUFFER,e.get(le).buffer))}function d(){return s.createVertexArray()}function p(T){return s.bindVertexArray(T)}function v(T){return s.deleteVertexArray(T)}function g(T,F,$){const ee=$.wireframe===!0;let le=r[T.id];le===void 0&&(le={},r[T.id]=le);let ne=le[F.id];ne===void 0&&(ne={},le[F.id]=ne);let ce=ne[ee];return ce===void 0&&(ce=_(d()),ne[ee]=ce),ce}function _(T){const F=[],$=[],ee=[];for(let le=0;le<t;le++)F[le]=0,$[le]=0,ee[le]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:F,enabledAttributes:$,attributeDivisors:ee,object:T,attributes:{},index:null}}function S(T,F,$,ee){const le=l.attributes,ne=F.attributes;let ce=0;const re=$.getAttributes();for(const V in re)if(re[V].location>=0){const ie=le[V];let P=ne[V];if(P===void 0&&(V==="instanceMatrix"&&T.instanceMatrix&&(P=T.instanceMatrix),V==="instanceColor"&&T.instanceColor&&(P=T.instanceColor)),ie===void 0||ie.attribute!==P||P&&ie.data!==P.data)return!0;ce++}return l.attributesNum!==ce||l.index!==ee}function M(T,F,$,ee){const le={},ne=F.attributes;let ce=0;const re=$.getAttributes();for(const V in re)if(re[V].location>=0){let ie=ne[V];ie===void 0&&(V==="instanceMatrix"&&T.instanceMatrix&&(ie=T.instanceMatrix),V==="instanceColor"&&T.instanceColor&&(ie=T.instanceColor));const P={};P.attribute=ie,ie&&ie.data&&(P.data=ie.data),le[V]=P,ce++}l.attributes=le,l.attributesNum=ce,l.index=ee}function A(){const T=l.newAttributes;for(let F=0,$=T.length;F<$;F++)T[F]=0}function y(T){x(T,0)}function x(T,F){const $=l.newAttributes,ee=l.enabledAttributes,le=l.attributeDivisors;$[T]=1,ee[T]===0&&(s.enableVertexAttribArray(T),ee[T]=1),le[T]!==F&&(s.vertexAttribDivisor(T,F),le[T]=F)}function O(){const T=l.newAttributes,F=l.enabledAttributes;for(let $=0,ee=F.length;$<ee;$++)F[$]!==T[$]&&(s.disableVertexAttribArray($),F[$]=0)}function D(T,F,$,ee,le,ne,ce){ce===!0?s.vertexAttribIPointer(T,F,$,le,ne):s.vertexAttribPointer(T,F,$,ee,le,ne)}function R(T,F,$,ee){A();const le=ee.attributes,ne=$.getAttributes(),ce=F.defaultAttributeValues;for(const re in ne){const V=ne[re];if(V.location>=0){let me=le[re];if(me===void 0&&(re==="instanceMatrix"&&T.instanceMatrix&&(me=T.instanceMatrix),re==="instanceColor"&&T.instanceColor&&(me=T.instanceColor)),me!==void 0){const ie=me.normalized,P=me.itemSize,B=e.get(me);if(B===void 0)continue;const Z=B.buffer,ue=B.type,he=B.bytesPerElement,K=ue===s.INT||ue===s.UNSIGNED_INT||me.gpuType===xd;if(me.isInterleavedBufferAttribute){const oe=me.data,Ee=oe.stride,ye=me.offset;if(oe.isInstancedInterleavedBuffer){for(let we=0;we<V.locationSize;we++)x(V.location+we,oe.meshPerAttribute);T.isInstancedMesh!==!0&&ee._maxInstanceCount===void 0&&(ee._maxInstanceCount=oe.meshPerAttribute*oe.count)}else for(let we=0;we<V.locationSize;we++)y(V.location+we);s.bindBuffer(s.ARRAY_BUFFER,Z);for(let we=0;we<V.locationSize;we++)D(V.location+we,P/V.locationSize,ue,ie,Ee*he,(ye+P/V.locationSize*we)*he,K)}else{if(me.isInstancedBufferAttribute){for(let oe=0;oe<V.locationSize;oe++)x(V.location+oe,me.meshPerAttribute);T.isInstancedMesh!==!0&&ee._maxInstanceCount===void 0&&(ee._maxInstanceCount=me.meshPerAttribute*me.count)}else for(let oe=0;oe<V.locationSize;oe++)y(V.location+oe);s.bindBuffer(s.ARRAY_BUFFER,Z);for(let oe=0;oe<V.locationSize;oe++)D(V.location+oe,P/V.locationSize,ue,ie,P*he,P/V.locationSize*oe*he,K)}}else if(ce!==void 0){const ie=ce[re];if(ie!==void 0)switch(ie.length){case 2:s.vertexAttrib2fv(V.location,ie);break;case 3:s.vertexAttrib3fv(V.location,ie);break;case 4:s.vertexAttrib4fv(V.location,ie);break;default:s.vertexAttrib1fv(V.location,ie)}}}}O()}function z(){N();for(const T in r){const F=r[T];for(const $ in F){const ee=F[$];for(const le in ee)v(ee[le].object),delete ee[le];delete F[$]}delete r[T]}}function H(T){if(r[T.id]===void 0)return;const F=r[T.id];for(const $ in F){const ee=F[$];for(const le in ee)v(ee[le].object),delete ee[le];delete F[$]}delete r[T.id]}function I(T){for(const F in r){const $=r[F];if($[T.id]===void 0)continue;const ee=$[T.id];for(const le in ee)v(ee[le].object),delete ee[le];delete $[T.id]}}function N(){C(),u=!0,l!==o&&(l=o,p(l.object))}function C(){o.geometry=null,o.program=null,o.wireframe=!1}return{setup:f,reset:N,resetDefaultState:C,dispose:z,releaseStatesOfGeometry:H,releaseStatesOfProgram:I,initAttributes:A,enableAttribute:y,disableUnusedAttributes:O}}function FM(s,e,t){let r;function o(p){r=p}function l(p,v){s.drawArrays(r,p,v),t.update(v,r,1)}function u(p,v,g){g!==0&&(s.drawArraysInstanced(r,p,v,g),t.update(v,r,g))}function f(p,v,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(r,p,0,v,0,g);let S=0;for(let M=0;M<g;M++)S+=v[M];t.update(S,r,1)}function d(p,v,g,_){if(g===0)return;const S=e.get("WEBGL_multi_draw");if(S===null)for(let M=0;M<p.length;M++)u(p[M],v[M],_[M]);else{S.multiDrawArraysInstancedWEBGL(r,p,0,v,0,_,0,g);let M=0;for(let A=0;A<g;A++)M+=v[A]*_[A];t.update(M,r,1)}}this.setMode=o,this.render=l,this.renderInstances=u,this.renderMultiDraw=f,this.renderMultiDrawInstances=d}function OM(s,e,t,r){let o;function l(){if(o!==void 0)return o;if(e.has("EXT_texture_filter_anisotropic")===!0){const I=e.get("EXT_texture_filter_anisotropic");o=s.getParameter(I.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else o=0;return o}function u(I){return!(I!==gi&&r.convert(I)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_FORMAT))}function f(I){const N=I===oa&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(I!==Ai&&r.convert(I)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_TYPE)&&I!==Xi&&!N)}function d(I){if(I==="highp"){if(s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.HIGH_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.HIGH_FLOAT).precision>0)return"highp";I="mediump"}return I==="mediump"&&s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.MEDIUM_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let p=t.precision!==void 0?t.precision:"highp";const v=d(p);v!==p&&(console.warn("THREE.WebGLRenderer:",p,"not supported, using",v,"instead."),p=v);const g=t.logarithmicDepthBuffer===!0,_=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control"),S=s.getParameter(s.MAX_TEXTURE_IMAGE_UNITS),M=s.getParameter(s.MAX_VERTEX_TEXTURE_IMAGE_UNITS),A=s.getParameter(s.MAX_TEXTURE_SIZE),y=s.getParameter(s.MAX_CUBE_MAP_TEXTURE_SIZE),x=s.getParameter(s.MAX_VERTEX_ATTRIBS),O=s.getParameter(s.MAX_VERTEX_UNIFORM_VECTORS),D=s.getParameter(s.MAX_VARYING_VECTORS),R=s.getParameter(s.MAX_FRAGMENT_UNIFORM_VECTORS),z=M>0,H=s.getParameter(s.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:l,getMaxPrecision:d,textureFormatReadable:u,textureTypeReadable:f,precision:p,logarithmicDepthBuffer:g,reversedDepthBuffer:_,maxTextures:S,maxVertexTextures:M,maxTextureSize:A,maxCubemapSize:y,maxAttributes:x,maxVertexUniforms:O,maxVaryings:D,maxFragmentUniforms:R,vertexTextures:z,maxSamples:H}}function kM(s){const e=this;let t=null,r=0,o=!1,l=!1;const u=new Jr,f=new Et,d={value:null,needsUpdate:!1};this.uniform=d,this.numPlanes=0,this.numIntersection=0,this.init=function(g,_){const S=g.length!==0||_||r!==0||o;return o=_,r=g.length,S},this.beginShadows=function(){l=!0,v(null)},this.endShadows=function(){l=!1},this.setGlobalState=function(g,_){t=v(g,_,0)},this.setState=function(g,_,S){const M=g.clippingPlanes,A=g.clipIntersection,y=g.clipShadows,x=s.get(g);if(!o||M===null||M.length===0||l&&!y)l?v(null):p();else{const O=l?0:r,D=O*4;let R=x.clippingState||null;d.value=R,R=v(M,_,D,S);for(let z=0;z!==D;++z)R[z]=t[z];x.clippingState=R,this.numIntersection=A?this.numPlanes:0,this.numPlanes+=O}};function p(){d.value!==t&&(d.value=t,d.needsUpdate=r>0),e.numPlanes=r,e.numIntersection=0}function v(g,_,S,M){const A=g!==null?g.length:0;let y=null;if(A!==0){if(y=d.value,M!==!0||y===null){const x=S+A*4,O=_.matrixWorldInverse;f.getNormalMatrix(O),(y===null||y.length<x)&&(y=new Float32Array(x));for(let D=0,R=S;D!==A;++D,R+=4)u.copy(g[D]).applyMatrix4(O,f),u.normal.toArray(y,R),y[R+3]=u.constant}d.value=y,d.needsUpdate=!0}return e.numPlanes=A,e.numIntersection=0,y}}function BM(s){let e=new WeakMap;function t(u,f){return f===Lf?u.mapping=Qs:f===Df&&(u.mapping=eo),u}function r(u){if(u&&u.isTexture){const f=u.mapping;if(f===Lf||f===Df)if(e.has(u)){const d=e.get(u).texture;return t(d,u.mapping)}else{const d=u.image;if(d&&d.height>0){const p=new ry(d.height);return p.fromEquirectangularTexture(s,u),e.set(u,p),u.addEventListener("dispose",o),t(p.texture,u.mapping)}else return null}}return u}function o(u){const f=u.target;f.removeEventListener("dispose",o);const d=e.get(f);d!==void 0&&(e.delete(f),d.dispose())}function l(){e=new WeakMap}return{get:r,dispose:l}}const Ys=4,Jm=[.125,.215,.35,.446,.526,.582],ns=20,gf=new hg,Qm=new It;let vf=null,_f=0,xf=0,yf=!1;const Qr=(1+Math.sqrt(5))/2,Xs=1/Qr,e0=[new Q(-Qr,Xs,0),new Q(Qr,Xs,0),new Q(-Xs,0,Qr),new Q(Xs,0,Qr),new Q(0,Qr,-Xs),new Q(0,Qr,Xs),new Q(-1,1,-1),new Q(1,1,-1),new Q(-1,1,1),new Q(1,1,1)],zM=new Q;class t0{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(e,t=0,r=.1,o=100,l={}){const{size:u=256,position:f=zM}=l;vf=this._renderer.getRenderTarget(),_f=this._renderer.getActiveCubeFace(),xf=this._renderer.getActiveMipmapLevel(),yf=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(u);const d=this._allocateTargets();return d.depthBuffer=!0,this._sceneToCubeUV(e,r,o,d,f),t>0&&this._blur(d,0,0,t),this._applyPMREM(d),this._cleanup(d),d}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=r0(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=i0(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose()}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodPlanes.length;e++)this._lodPlanes[e].dispose()}_cleanup(e){this._renderer.setRenderTarget(vf,_f,xf),this._renderer.xr.enabled=yf,e.scissorTest=!1,Ol(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Qs||e.mapping===eo?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),vf=this._renderer.getRenderTarget(),_f=this._renderer.getActiveCubeFace(),xf=this._renderer.getActiveMipmapLevel(),yf=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const r=t||this._allocateTargets();return this._textureToCubeUV(e,r),this._applyPMREM(r),this._cleanup(r),r}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,r={magFilter:Ei,minFilter:Ei,generateMipmaps:!1,type:oa,format:gi,colorSpace:to,depthBuffer:!1},o=n0(e,t,r);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=n0(e,t,r);const{_lodMax:l}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=HM(l)),this._blurMaterial=VM(l,e,t)}return o}_compileMaterial(e){const t=new an(this._lodPlanes[0],e);this._renderer.compile(t,gf)}_sceneToCubeUV(e,t,r,o,l){const d=new ri(90,1,t,r),p=[1,-1,1,1,1,1],v=[1,1,1,-1,-1,-1],g=this._renderer,_=g.autoClear,S=g.toneMapping;g.getClearColor(Qm),g.toneMapping=Rr,g.autoClear=!1,g.state.buffers.depth.getReversed()&&(g.setRenderTarget(o),g.clearDepth(),g.setRenderTarget(null));const A=new Jl({name:"PMREM.Background",side:Gn,depthWrite:!1,depthTest:!1}),y=new an(new ji,A);let x=!1;const O=e.background;O?O.isColor&&(A.color.copy(O),e.background=null,x=!0):(A.color.copy(Qm),x=!0);for(let D=0;D<6;D++){const R=D%3;R===0?(d.up.set(0,p[D],0),d.position.set(l.x,l.y,l.z),d.lookAt(l.x+v[D],l.y,l.z)):R===1?(d.up.set(0,0,p[D]),d.position.set(l.x,l.y,l.z),d.lookAt(l.x,l.y+v[D],l.z)):(d.up.set(0,p[D],0),d.position.set(l.x,l.y,l.z),d.lookAt(l.x,l.y,l.z+v[D]));const z=this._cubeSize;Ol(o,R*z,D>2?z:0,z,z),g.setRenderTarget(o),x&&g.render(y,d),g.render(e,d)}y.geometry.dispose(),y.material.dispose(),g.toneMapping=S,g.autoClear=_,e.background=O}_textureToCubeUV(e,t){const r=this._renderer,o=e.mapping===Qs||e.mapping===eo;o?(this._cubemapMaterial===null&&(this._cubemapMaterial=r0()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=i0());const l=o?this._cubemapMaterial:this._equirectMaterial,u=new an(this._lodPlanes[0],l),f=l.uniforms;f.envMap.value=e;const d=this._cubeSize;Ol(t,0,0,3*d,2*d),r.setRenderTarget(t),r.render(u,gf)}_applyPMREM(e){const t=this._renderer,r=t.autoClear;t.autoClear=!1;const o=this._lodPlanes.length;for(let l=1;l<o;l++){const u=Math.sqrt(this._sigmas[l]*this._sigmas[l]-this._sigmas[l-1]*this._sigmas[l-1]),f=e0[(o-l-1)%e0.length];this._blur(e,l-1,l,u,f)}t.autoClear=r}_blur(e,t,r,o,l){const u=this._pingPongRenderTarget;this._halfBlur(e,u,t,r,o,"latitudinal",l),this._halfBlur(u,e,r,r,o,"longitudinal",l)}_halfBlur(e,t,r,o,l,u,f){const d=this._renderer,p=this._blurMaterial;u!=="latitudinal"&&u!=="longitudinal"&&console.error("blur direction must be either latitudinal or longitudinal!");const v=3,g=new an(this._lodPlanes[o],p),_=p.uniforms,S=this._sizeLods[r]-1,M=isFinite(l)?Math.PI/(2*S):2*Math.PI/(2*ns-1),A=l/M,y=isFinite(l)?1+Math.floor(v*A):ns;y>ns&&console.warn(`sigmaRadians, ${l}, is too large and will clip, as it requested ${y} samples when the maximum is set to ${ns}`);const x=[];let O=0;for(let I=0;I<ns;++I){const N=I/A,C=Math.exp(-N*N/2);x.push(C),I===0?O+=C:I<y&&(O+=2*C)}for(let I=0;I<x.length;I++)x[I]=x[I]/O;_.envMap.value=e.texture,_.samples.value=y,_.weights.value=x,_.latitudinal.value=u==="latitudinal",f&&(_.poleAxis.value=f);const{_lodMax:D}=this;_.dTheta.value=M,_.mipInt.value=D-r;const R=this._sizeLods[o],z=3*R*(o>D-Ys?o-D+Ys:0),H=4*(this._cubeSize-R);Ol(t,z,H,3*R,2*R),d.setRenderTarget(t),d.render(g,gf)}}function HM(s){const e=[],t=[],r=[];let o=s;const l=s-Ys+1+Jm.length;for(let u=0;u<l;u++){const f=Math.pow(2,o);t.push(f);let d=1/f;u>s-Ys?d=Jm[u-s+Ys-1]:u===0&&(d=0),r.push(d);const p=1/(f-2),v=-p,g=1+p,_=[v,v,g,v,g,g,v,v,g,g,v,g],S=6,M=6,A=3,y=2,x=1,O=new Float32Array(A*M*S),D=new Float32Array(y*M*S),R=new Float32Array(x*M*S);for(let H=0;H<S;H++){const I=H%3*2/3-1,N=H>2?0:-1,C=[I,N,0,I+2/3,N,0,I+2/3,N+1,0,I,N,0,I+2/3,N+1,0,I,N+1,0];O.set(C,A*M*H),D.set(_,y*M*H);const T=[H,H,H,H,H,H];R.set(T,x*M*H)}const z=new Ci;z.setAttribute("position",new Ti(O,A)),z.setAttribute("uv",new Ti(D,y)),z.setAttribute("faceIndex",new Ti(R,x)),e.push(z),o>Ys&&o--}return{lodPlanes:e,sizeLods:t,sigmas:r}}function n0(s,e,t){const r=new os(s,e,t);return r.texture.mapping=nc,r.texture.name="PMREM.cubeUv",r.scissorTest=!0,r}function Ol(s,e,t,r,o){s.viewport.set(e,t,r,o),s.scissor.set(e,t,r,o)}function VM(s,e,t){const r=new Float32Array(ns),o=new Q(0,1,0);return new br({name:"SphericalGaussianBlur",defines:{n:ns,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${s}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:r},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:o}},vertexShader:Id(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:Ar,depthTest:!1,depthWrite:!1})}function i0(){return new br({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Id(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Ar,depthTest:!1,depthWrite:!1})}function r0(){return new br({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Id(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Ar,depthTest:!1,depthWrite:!1})}function Id(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function GM(s){let e=new WeakMap,t=null;function r(f){if(f&&f.isTexture){const d=f.mapping,p=d===Lf||d===Df,v=d===Qs||d===eo;if(p||v){let g=e.get(f);const _=g!==void 0?g.texture.pmremVersion:0;if(f.isRenderTargetTexture&&f.pmremVersion!==_)return t===null&&(t=new t0(s)),g=p?t.fromEquirectangular(f,g):t.fromCubemap(f,g),g.texture.pmremVersion=f.pmremVersion,e.set(f,g),g.texture;if(g!==void 0)return g.texture;{const S=f.image;return p&&S&&S.height>0||v&&S&&o(S)?(t===null&&(t=new t0(s)),g=p?t.fromEquirectangular(f):t.fromCubemap(f),g.texture.pmremVersion=f.pmremVersion,e.set(f,g),f.addEventListener("dispose",l),g.texture):null}}}return f}function o(f){let d=0;const p=6;for(let v=0;v<p;v++)f[v]!==void 0&&d++;return d===p}function l(f){const d=f.target;d.removeEventListener("dispose",l);const p=e.get(d);p!==void 0&&(e.delete(d),p.dispose())}function u(){e=new WeakMap,t!==null&&(t.dispose(),t=null)}return{get:r,dispose:u}}function WM(s){const e={};function t(r){if(e[r]!==void 0)return e[r];let o;switch(r){case"WEBGL_depth_texture":o=s.getExtension("WEBGL_depth_texture")||s.getExtension("MOZ_WEBGL_depth_texture")||s.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":o=s.getExtension("EXT_texture_filter_anisotropic")||s.getExtension("MOZ_EXT_texture_filter_anisotropic")||s.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":o=s.getExtension("WEBGL_compressed_texture_s3tc")||s.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||s.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":o=s.getExtension("WEBGL_compressed_texture_pvrtc")||s.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:o=s.getExtension(r)}return e[r]=o,o}return{has:function(r){return t(r)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(r){const o=t(r);return o===null&&na("THREE.WebGLRenderer: "+r+" extension not supported."),o}}}function XM(s,e,t,r){const o={},l=new WeakMap;function u(g){const _=g.target;_.index!==null&&e.remove(_.index);for(const M in _.attributes)e.remove(_.attributes[M]);_.removeEventListener("dispose",u),delete o[_.id];const S=l.get(_);S&&(e.remove(S),l.delete(_)),r.releaseStatesOfGeometry(_),_.isInstancedBufferGeometry===!0&&delete _._maxInstanceCount,t.memory.geometries--}function f(g,_){return o[_.id]===!0||(_.addEventListener("dispose",u),o[_.id]=!0,t.memory.geometries++),_}function d(g){const _=g.attributes;for(const S in _)e.update(_[S],s.ARRAY_BUFFER)}function p(g){const _=[],S=g.index,M=g.attributes.position;let A=0;if(S!==null){const O=S.array;A=S.version;for(let D=0,R=O.length;D<R;D+=3){const z=O[D+0],H=O[D+1],I=O[D+2];_.push(z,H,H,I,I,z)}}else if(M!==void 0){const O=M.array;A=M.version;for(let D=0,R=O.length/3-1;D<R;D+=3){const z=D+0,H=D+1,I=D+2;_.push(z,H,H,I,I,z)}}else return;const y=new(q0(_)?J0:Z0)(_,1);y.version=A;const x=l.get(g);x&&e.remove(x),l.set(g,y)}function v(g){const _=l.get(g);if(_){const S=g.index;S!==null&&_.version<S.version&&p(g)}else p(g);return l.get(g)}return{get:f,update:d,getWireframeAttribute:v}}function jM(s,e,t){let r;function o(_){r=_}let l,u;function f(_){l=_.type,u=_.bytesPerElement}function d(_,S){s.drawElements(r,S,l,_*u),t.update(S,r,1)}function p(_,S,M){M!==0&&(s.drawElementsInstanced(r,S,l,_*u,M),t.update(S,r,M))}function v(_,S,M){if(M===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(r,S,0,l,_,0,M);let y=0;for(let x=0;x<M;x++)y+=S[x];t.update(y,r,1)}function g(_,S,M,A){if(M===0)return;const y=e.get("WEBGL_multi_draw");if(y===null)for(let x=0;x<_.length;x++)p(_[x]/u,S[x],A[x]);else{y.multiDrawElementsInstancedWEBGL(r,S,0,l,_,0,A,0,M);let x=0;for(let O=0;O<M;O++)x+=S[O]*A[O];t.update(x,r,1)}}this.setMode=o,this.setIndex=f,this.render=d,this.renderInstances=p,this.renderMultiDraw=v,this.renderMultiDrawInstances=g}function qM(s){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function r(l,u,f){switch(t.calls++,u){case s.TRIANGLES:t.triangles+=f*(l/3);break;case s.LINES:t.lines+=f*(l/2);break;case s.LINE_STRIP:t.lines+=f*(l-1);break;case s.LINE_LOOP:t.lines+=f*l;break;case s.POINTS:t.points+=f*l;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",u);break}}function o(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:o,update:r}}function YM(s,e,t){const r=new WeakMap,o=new Zt;function l(u,f,d){const p=u.morphTargetInfluences,v=f.morphAttributes.position||f.morphAttributes.normal||f.morphAttributes.color,g=v!==void 0?v.length:0;let _=r.get(f);if(_===void 0||_.count!==g){let T=function(){N.dispose(),r.delete(f),f.removeEventListener("dispose",T)};var S=T;_!==void 0&&_.texture.dispose();const M=f.morphAttributes.position!==void 0,A=f.morphAttributes.normal!==void 0,y=f.morphAttributes.color!==void 0,x=f.morphAttributes.position||[],O=f.morphAttributes.normal||[],D=f.morphAttributes.color||[];let R=0;M===!0&&(R=1),A===!0&&(R=2),y===!0&&(R=3);let z=f.attributes.position.count*R,H=1;z>e.maxTextureSize&&(H=Math.ceil(z/e.maxTextureSize),z=e.maxTextureSize);const I=new Float32Array(z*H*4*g),N=new Y0(I,z,H,g);N.type=Xi,N.needsUpdate=!0;const C=R*4;for(let F=0;F<g;F++){const $=x[F],ee=O[F],le=D[F],ne=z*H*4*F;for(let ce=0;ce<$.count;ce++){const re=ce*C;M===!0&&(o.fromBufferAttribute($,ce),I[ne+re+0]=o.x,I[ne+re+1]=o.y,I[ne+re+2]=o.z,I[ne+re+3]=0),A===!0&&(o.fromBufferAttribute(ee,ce),I[ne+re+4]=o.x,I[ne+re+5]=o.y,I[ne+re+6]=o.z,I[ne+re+7]=0),y===!0&&(o.fromBufferAttribute(le,ce),I[ne+re+8]=o.x,I[ne+re+9]=o.y,I[ne+re+10]=o.z,I[ne+re+11]=le.itemSize===4?o.w:1)}}_={count:g,texture:N,size:new Ge(z,H)},r.set(f,_),f.addEventListener("dispose",T)}if(u.isInstancedMesh===!0&&u.morphTexture!==null)d.getUniforms().setValue(s,"morphTexture",u.morphTexture,t);else{let M=0;for(let y=0;y<p.length;y++)M+=p[y];const A=f.morphTargetsRelative?1:1-M;d.getUniforms().setValue(s,"morphTargetBaseInfluence",A),d.getUniforms().setValue(s,"morphTargetInfluences",p)}d.getUniforms().setValue(s,"morphTargetsTexture",_.texture,t),d.getUniforms().setValue(s,"morphTargetsTextureSize",_.size)}return{update:l}}function $M(s,e,t,r){let o=new WeakMap;function l(d){const p=r.render.frame,v=d.geometry,g=e.get(d,v);if(o.get(g)!==p&&(e.update(g),o.set(g,p)),d.isInstancedMesh&&(d.hasEventListener("dispose",f)===!1&&d.addEventListener("dispose",f),o.get(d)!==p&&(t.update(d.instanceMatrix,s.ARRAY_BUFFER),d.instanceColor!==null&&t.update(d.instanceColor,s.ARRAY_BUFFER),o.set(d,p))),d.isSkinnedMesh){const _=d.skeleton;o.get(_)!==p&&(_.update(),o.set(_,p))}return g}function u(){o=new WeakMap}function f(d){const p=d.target;p.removeEventListener("dispose",f),t.remove(p.instanceMatrix),p.instanceColor!==null&&t.remove(p.instanceColor)}return{update:l,dispose:u}}const mg=new Nn,s0=new ng(1,1),gg=new Y0,vg=new Hx,_g=new tg,o0=[],a0=[],l0=new Float32Array(16),c0=new Float32Array(9),u0=new Float32Array(4);function ao(s,e,t){const r=s[0];if(r<=0||r>0)return s;const o=e*t;let l=o0[o];if(l===void 0&&(l=new Float32Array(o),o0[o]=l),e!==0){r.toArray(l,0);for(let u=1,f=0;u!==e;++u)f+=t,s[u].toArray(l,f)}return l}function ln(s,e){if(s.length!==e.length)return!1;for(let t=0,r=s.length;t<r;t++)if(s[t]!==e[t])return!1;return!0}function cn(s,e){for(let t=0,r=e.length;t<r;t++)s[t]=e[t]}function ic(s,e){let t=a0[e];t===void 0&&(t=new Int32Array(e),a0[e]=t);for(let r=0;r!==e;++r)t[r]=s.allocateTextureUnit();return t}function KM(s,e){const t=this.cache;t[0]!==e&&(s.uniform1f(this.addr,e),t[0]=e)}function ZM(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(s.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(ln(t,e))return;s.uniform2fv(this.addr,e),cn(t,e)}}function JM(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(s.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(s.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(ln(t,e))return;s.uniform3fv(this.addr,e),cn(t,e)}}function QM(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(s.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(ln(t,e))return;s.uniform4fv(this.addr,e),cn(t,e)}}function eE(s,e){const t=this.cache,r=e.elements;if(r===void 0){if(ln(t,e))return;s.uniformMatrix2fv(this.addr,!1,e),cn(t,e)}else{if(ln(t,r))return;u0.set(r),s.uniformMatrix2fv(this.addr,!1,u0),cn(t,r)}}function tE(s,e){const t=this.cache,r=e.elements;if(r===void 0){if(ln(t,e))return;s.uniformMatrix3fv(this.addr,!1,e),cn(t,e)}else{if(ln(t,r))return;c0.set(r),s.uniformMatrix3fv(this.addr,!1,c0),cn(t,r)}}function nE(s,e){const t=this.cache,r=e.elements;if(r===void 0){if(ln(t,e))return;s.uniformMatrix4fv(this.addr,!1,e),cn(t,e)}else{if(ln(t,r))return;l0.set(r),s.uniformMatrix4fv(this.addr,!1,l0),cn(t,r)}}function iE(s,e){const t=this.cache;t[0]!==e&&(s.uniform1i(this.addr,e),t[0]=e)}function rE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(s.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(ln(t,e))return;s.uniform2iv(this.addr,e),cn(t,e)}}function sE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(s.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(ln(t,e))return;s.uniform3iv(this.addr,e),cn(t,e)}}function oE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(s.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(ln(t,e))return;s.uniform4iv(this.addr,e),cn(t,e)}}function aE(s,e){const t=this.cache;t[0]!==e&&(s.uniform1ui(this.addr,e),t[0]=e)}function lE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(s.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(ln(t,e))return;s.uniform2uiv(this.addr,e),cn(t,e)}}function cE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(s.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(ln(t,e))return;s.uniform3uiv(this.addr,e),cn(t,e)}}function uE(s,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(s.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(ln(t,e))return;s.uniform4uiv(this.addr,e),cn(t,e)}}function fE(s,e,t){const r=this.cache,o=t.allocateTextureUnit();r[0]!==o&&(s.uniform1i(this.addr,o),r[0]=o);let l;this.type===s.SAMPLER_2D_SHADOW?(s0.compareFunction=j0,l=s0):l=mg,t.setTexture2D(e||l,o)}function dE(s,e,t){const r=this.cache,o=t.allocateTextureUnit();r[0]!==o&&(s.uniform1i(this.addr,o),r[0]=o),t.setTexture3D(e||vg,o)}function hE(s,e,t){const r=this.cache,o=t.allocateTextureUnit();r[0]!==o&&(s.uniform1i(this.addr,o),r[0]=o),t.setTextureCube(e||_g,o)}function pE(s,e,t){const r=this.cache,o=t.allocateTextureUnit();r[0]!==o&&(s.uniform1i(this.addr,o),r[0]=o),t.setTexture2DArray(e||gg,o)}function mE(s){switch(s){case 5126:return KM;case 35664:return ZM;case 35665:return JM;case 35666:return QM;case 35674:return eE;case 35675:return tE;case 35676:return nE;case 5124:case 35670:return iE;case 35667:case 35671:return rE;case 35668:case 35672:return sE;case 35669:case 35673:return oE;case 5125:return aE;case 36294:return lE;case 36295:return cE;case 36296:return uE;case 35678:case 36198:case 36298:case 36306:case 35682:return fE;case 35679:case 36299:case 36307:return dE;case 35680:case 36300:case 36308:case 36293:return hE;case 36289:case 36303:case 36311:case 36292:return pE}}function gE(s,e){s.uniform1fv(this.addr,e)}function vE(s,e){const t=ao(e,this.size,2);s.uniform2fv(this.addr,t)}function _E(s,e){const t=ao(e,this.size,3);s.uniform3fv(this.addr,t)}function xE(s,e){const t=ao(e,this.size,4);s.uniform4fv(this.addr,t)}function yE(s,e){const t=ao(e,this.size,4);s.uniformMatrix2fv(this.addr,!1,t)}function SE(s,e){const t=ao(e,this.size,9);s.uniformMatrix3fv(this.addr,!1,t)}function ME(s,e){const t=ao(e,this.size,16);s.uniformMatrix4fv(this.addr,!1,t)}function EE(s,e){s.uniform1iv(this.addr,e)}function wE(s,e){s.uniform2iv(this.addr,e)}function TE(s,e){s.uniform3iv(this.addr,e)}function AE(s,e){s.uniform4iv(this.addr,e)}function RE(s,e){s.uniform1uiv(this.addr,e)}function CE(s,e){s.uniform2uiv(this.addr,e)}function bE(s,e){s.uniform3uiv(this.addr,e)}function PE(s,e){s.uniform4uiv(this.addr,e)}function LE(s,e,t){const r=this.cache,o=e.length,l=ic(t,o);ln(r,l)||(s.uniform1iv(this.addr,l),cn(r,l));for(let u=0;u!==o;++u)t.setTexture2D(e[u]||mg,l[u])}function DE(s,e,t){const r=this.cache,o=e.length,l=ic(t,o);ln(r,l)||(s.uniform1iv(this.addr,l),cn(r,l));for(let u=0;u!==o;++u)t.setTexture3D(e[u]||vg,l[u])}function NE(s,e,t){const r=this.cache,o=e.length,l=ic(t,o);ln(r,l)||(s.uniform1iv(this.addr,l),cn(r,l));for(let u=0;u!==o;++u)t.setTextureCube(e[u]||_g,l[u])}function IE(s,e,t){const r=this.cache,o=e.length,l=ic(t,o);ln(r,l)||(s.uniform1iv(this.addr,l),cn(r,l));for(let u=0;u!==o;++u)t.setTexture2DArray(e[u]||gg,l[u])}function UE(s){switch(s){case 5126:return gE;case 35664:return vE;case 35665:return _E;case 35666:return xE;case 35674:return yE;case 35675:return SE;case 35676:return ME;case 5124:case 35670:return EE;case 35667:case 35671:return wE;case 35668:case 35672:return TE;case 35669:case 35673:return AE;case 5125:return RE;case 36294:return CE;case 36295:return bE;case 36296:return PE;case 35678:case 36198:case 36298:case 36306:case 35682:return LE;case 35679:case 36299:case 36307:return DE;case 35680:case 36300:case 36308:case 36293:return NE;case 36289:case 36303:case 36311:case 36292:return IE}}class FE{constructor(e,t,r){this.id=e,this.addr=r,this.cache=[],this.type=t.type,this.setValue=mE(t.type)}}class OE{constructor(e,t,r){this.id=e,this.addr=r,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=UE(t.type)}}class kE{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,r){const o=this.seq;for(let l=0,u=o.length;l!==u;++l){const f=o[l];f.setValue(e,t[f.id],r)}}}const Sf=/(\w+)(\])?(\[|\.)?/g;function f0(s,e){s.seq.push(e),s.map[e.id]=e}function BE(s,e,t){const r=s.name,o=r.length;for(Sf.lastIndex=0;;){const l=Sf.exec(r),u=Sf.lastIndex;let f=l[1];const d=l[2]==="]",p=l[3];if(d&&(f=f|0),p===void 0||p==="["&&u+2===o){f0(t,p===void 0?new FE(f,s,e):new OE(f,s,e));break}else{let g=t.map[f];g===void 0&&(g=new kE(f),f0(t,g)),t=g}}}class ql{constructor(e,t){this.seq=[],this.map={};const r=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let o=0;o<r;++o){const l=e.getActiveUniform(t,o),u=e.getUniformLocation(t,l.name);BE(l,u,this)}}setValue(e,t,r,o){const l=this.map[t];l!==void 0&&l.setValue(e,r,o)}setOptional(e,t,r){const o=t[r];o!==void 0&&this.setValue(e,r,o)}static upload(e,t,r,o){for(let l=0,u=t.length;l!==u;++l){const f=t[l],d=r[f.id];d.needsUpdate!==!1&&f.setValue(e,d.value,o)}}static seqWithValue(e,t){const r=[];for(let o=0,l=e.length;o!==l;++o){const u=e[o];u.id in t&&r.push(u)}return r}}function d0(s,e,t){const r=s.createShader(e);return s.shaderSource(r,t),s.compileShader(r),r}const zE=37297;let HE=0;function VE(s,e){const t=s.split(`
`),r=[],o=Math.max(e-6,0),l=Math.min(e+6,t.length);for(let u=o;u<l;u++){const f=u+1;r.push(`${f===e?">":" "} ${f}: ${t[u]}`)}return r.join(`
`)}const h0=new Et;function GE(s){Nt._getMatrix(h0,Nt.workingColorSpace,s);const e=`mat3( ${h0.elements.map(t=>t.toFixed(4))} )`;switch(Nt.getTransfer(s)){case $l:return[e,"LinearTransferOETF"];case kt:return[e,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",s),[e,"LinearTransferOETF"]}}function p0(s,e,t){const r=s.getShaderParameter(e,s.COMPILE_STATUS),l=(s.getShaderInfoLog(e)||"").trim();if(r&&l==="")return"";const u=/ERROR: 0:(\d+)/.exec(l);if(u){const f=parseInt(u[1]);return t.toUpperCase()+`

`+l+`

`+VE(s.getShaderSource(e),f)}else return l}function WE(s,e){const t=GE(e);return[`vec4 ${s}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}function XE(s,e){let t;switch(e){case mx:t="Linear";break;case gx:t="Reinhard";break;case vx:t="Cineon";break;case _x:t="ACESFilmic";break;case yx:t="AgX";break;case Sx:t="Neutral";break;case xx:t="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",e),t="Linear"}return"vec3 "+s+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const kl=new Q;function jE(){Nt.getLuminanceCoefficients(kl);const s=kl.x.toFixed(4),e=kl.y.toFixed(4),t=kl.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${s}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function qE(s){return[s.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",s.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Yo).join(`
`)}function YE(s){const e=[];for(const t in s){const r=s[t];r!==!1&&e.push("#define "+t+" "+r)}return e.join(`
`)}function $E(s,e){const t={},r=s.getProgramParameter(e,s.ACTIVE_ATTRIBUTES);for(let o=0;o<r;o++){const l=s.getActiveAttrib(e,o),u=l.name;let f=1;l.type===s.FLOAT_MAT2&&(f=2),l.type===s.FLOAT_MAT3&&(f=3),l.type===s.FLOAT_MAT4&&(f=4),t[u]={type:l.type,location:s.getAttribLocation(e,u),locationSize:f}}return t}function Yo(s){return s!==""}function m0(s,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return s.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function g0(s,e){return s.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const KE=/^[ \t]*#include +<([\w\d./]+)>/gm;function pd(s){return s.replace(KE,JE)}const ZE=new Map;function JE(s,e){let t=wt[e];if(t===void 0){const r=ZE.get(e);if(r!==void 0)t=wt[r],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,r);else throw new Error("Can not resolve #include <"+e+">")}return pd(t)}const QE=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function v0(s){return s.replace(QE,ew)}function ew(s,e,t,r){let o="";for(let l=parseInt(e);l<parseInt(t);l++)o+=r.replace(/\[\s*i\s*\]/g,"[ "+l+" ]").replace(/UNROLLED_LOOP_INDEX/g,l);return o}function _0(s){let e=`precision ${s.precision} float;
	precision ${s.precision} int;
	precision ${s.precision} sampler2D;
	precision ${s.precision} samplerCube;
	precision ${s.precision} sampler3D;
	precision ${s.precision} sampler2DArray;
	precision ${s.precision} sampler2DShadow;
	precision ${s.precision} samplerCubeShadow;
	precision ${s.precision} sampler2DArrayShadow;
	precision ${s.precision} isampler2D;
	precision ${s.precision} isampler3D;
	precision ${s.precision} isamplerCube;
	precision ${s.precision} isampler2DArray;
	precision ${s.precision} usampler2D;
	precision ${s.precision} usampler3D;
	precision ${s.precision} usamplerCube;
	precision ${s.precision} usampler2DArray;
	`;return s.precision==="highp"?e+=`
#define HIGH_PRECISION`:s.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:s.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}function tw(s){let e="SHADOWMAP_TYPE_BASIC";return s.shadowMapType===I0?e="SHADOWMAP_TYPE_PCF":s.shadowMapType===Y_?e="SHADOWMAP_TYPE_PCF_SOFT":s.shadowMapType===Gi&&(e="SHADOWMAP_TYPE_VSM"),e}function nw(s){let e="ENVMAP_TYPE_CUBE";if(s.envMap)switch(s.envMapMode){case Qs:case eo:e="ENVMAP_TYPE_CUBE";break;case nc:e="ENVMAP_TYPE_CUBE_UV";break}return e}function iw(s){let e="ENVMAP_MODE_REFLECTION";if(s.envMap)switch(s.envMapMode){case eo:e="ENVMAP_MODE_REFRACTION";break}return e}function rw(s){let e="ENVMAP_BLENDING_NONE";if(s.envMap)switch(s.combine){case U0:e="ENVMAP_BLENDING_MULTIPLY";break;case hx:e="ENVMAP_BLENDING_MIX";break;case px:e="ENVMAP_BLENDING_ADD";break}return e}function sw(s){const e=s.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,r=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:r,maxMip:t}}function ow(s,e,t,r){const o=s.getContext(),l=t.defines;let u=t.vertexShader,f=t.fragmentShader;const d=tw(t),p=nw(t),v=iw(t),g=rw(t),_=sw(t),S=qE(t),M=YE(l),A=o.createProgram();let y,x,O=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(y=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,M].filter(Yo).join(`
`),y.length>0&&(y+=`
`),x=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,M].filter(Yo).join(`
`),x.length>0&&(x+=`
`)):(y=[_0(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,M,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+v:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+d:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Yo).join(`
`),x=[_0(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,M,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+p:"",t.envMap?"#define "+v:"",t.envMap?"#define "+g:"",_?"#define CUBEUV_TEXEL_WIDTH "+_.texelWidth:"",_?"#define CUBEUV_TEXEL_HEIGHT "+_.texelHeight:"",_?"#define CUBEUV_MAX_MIP "+_.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor||t.batchingColor?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+d:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Rr?"#define TONE_MAPPING":"",t.toneMapping!==Rr?wt.tonemapping_pars_fragment:"",t.toneMapping!==Rr?XE("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",wt.colorspace_pars_fragment,WE("linearToOutputTexel",t.outputColorSpace),jE(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Yo).join(`
`)),u=pd(u),u=m0(u,t),u=g0(u,t),f=pd(f),f=m0(f,t),f=g0(f,t),u=v0(u),f=v0(f),t.isRawShaderMaterial!==!0&&(O=`#version 300 es
`,y=[S,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+y,x=["#define varying in",t.glslVersion===Em?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===Em?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+x);const D=O+y+u,R=O+x+f,z=d0(o,o.VERTEX_SHADER,D),H=d0(o,o.FRAGMENT_SHADER,R);o.attachShader(A,z),o.attachShader(A,H),t.index0AttributeName!==void 0?o.bindAttribLocation(A,0,t.index0AttributeName):t.morphTargets===!0&&o.bindAttribLocation(A,0,"position"),o.linkProgram(A);function I(F){if(s.debug.checkShaderErrors){const $=o.getProgramInfoLog(A)||"",ee=o.getShaderInfoLog(z)||"",le=o.getShaderInfoLog(H)||"",ne=$.trim(),ce=ee.trim(),re=le.trim();let V=!0,me=!0;if(o.getProgramParameter(A,o.LINK_STATUS)===!1)if(V=!1,typeof s.debug.onShaderError=="function")s.debug.onShaderError(o,A,z,H);else{const ie=p0(o,z,"vertex"),P=p0(o,H,"fragment");console.error("THREE.WebGLProgram: Shader Error "+o.getError()+" - VALIDATE_STATUS "+o.getProgramParameter(A,o.VALIDATE_STATUS)+`

Material Name: `+F.name+`
Material Type: `+F.type+`

Program Info Log: `+ne+`
`+ie+`
`+P)}else ne!==""?console.warn("THREE.WebGLProgram: Program Info Log:",ne):(ce===""||re==="")&&(me=!1);me&&(F.diagnostics={runnable:V,programLog:ne,vertexShader:{log:ce,prefix:y},fragmentShader:{log:re,prefix:x}})}o.deleteShader(z),o.deleteShader(H),N=new ql(o,A),C=$E(o,A)}let N;this.getUniforms=function(){return N===void 0&&I(this),N};let C;this.getAttributes=function(){return C===void 0&&I(this),C};let T=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return T===!1&&(T=o.getProgramParameter(A,zE)),T},this.destroy=function(){r.releaseStatesOfProgram(this),o.deleteProgram(A),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=HE++,this.cacheKey=e,this.usedTimes=1,this.program=A,this.vertexShader=z,this.fragmentShader=H,this}let aw=0;class lw{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const t=e.vertexShader,r=e.fragmentShader,o=this._getShaderStage(t),l=this._getShaderStage(r),u=this._getShaderCacheForMaterial(e);return u.has(o)===!1&&(u.add(o),o.usedTimes++),u.has(l)===!1&&(u.add(l),l.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const r of t)r.usedTimes--,r.usedTimes===0&&this.shaderCache.delete(r.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let r=t.get(e);return r===void 0&&(r=new Set,t.set(e,r)),r}_getShaderStage(e){const t=this.shaderCache;let r=t.get(e);return r===void 0&&(r=new cw(e),t.set(e,r)),r}}class cw{constructor(e){this.id=aw++,this.code=e,this.usedTimes=0}}function uw(s,e,t,r,o,l,u){const f=new Rd,d=new lw,p=new Set,v=[],g=o.logarithmicDepthBuffer,_=o.vertexTextures;let S=o.precision;const M={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function A(C){return p.add(C),C===0?"uv":`uv${C}`}function y(C,T,F,$,ee){const le=$.fog,ne=ee.geometry,ce=C.isMeshStandardMaterial?$.environment:null,re=(C.isMeshStandardMaterial?t:e).get(C.envMap||ce),V=re&&re.mapping===nc?re.image.height:null,me=M[C.type];C.precision!==null&&(S=o.getMaxPrecision(C.precision),S!==C.precision&&console.warn("THREE.WebGLProgram.getParameters:",C.precision,"not supported, using",S,"instead."));const ie=ne.morphAttributes.position||ne.morphAttributes.normal||ne.morphAttributes.color,P=ie!==void 0?ie.length:0;let B=0;ne.morphAttributes.position!==void 0&&(B=1),ne.morphAttributes.normal!==void 0&&(B=2),ne.morphAttributes.color!==void 0&&(B=3);let Z,ue,he,K;if(me){const qe=Mi[me];Z=qe.vertexShader,ue=qe.fragmentShader}else Z=C.vertexShader,ue=C.fragmentShader,d.update(C),he=d.getVertexShaderID(C),K=d.getFragmentShaderID(C);const oe=s.getRenderTarget(),Ee=s.state.buffers.depth.getReversed(),ye=ee.isInstancedMesh===!0,we=ee.isBatchedMesh===!0,tt=!!C.map,at=!!C.matcap,U=!!re,Me=!!C.aoMap,_e=!!C.lightMap,Se=!!C.bumpMap,fe=!!C.normalMap,be=!!C.displacementMap,xe=!!C.emissiveMap,Re=!!C.metalnessMap,ct=!!C.roughnessMap,ft=C.anisotropy>0,L=C.clearcoat>0,w=C.dispersion>0,J=C.iridescence>0,ge=C.sheen>0,Ae=C.transmission>0,ve=ft&&!!C.anisotropyMap,Je=L&&!!C.clearcoatMap,Le=L&&!!C.clearcoatNormalMap,Ke=L&&!!C.clearcoatRoughnessMap,nt=J&&!!C.iridescenceMap,Ie=J&&!!C.iridescenceThicknessMap,He=ge&&!!C.sheenColorMap,ut=ge&&!!C.sheenRoughnessMap,Ze=!!C.specularMap,Ve=!!C.specularColorMap,ht=!!C.specularIntensityMap,X=Ae&&!!C.transmissionMap,Ue=Ae&&!!C.thicknessMap,ke=!!C.gradientMap,Xe=!!C.alphaMap,De=C.alphaTest>0,Te=!!C.alphaHash,et=!!C.extensions;let xt=Rr;C.toneMapped&&(oe===null||oe.isXRRenderTarget===!0)&&(xt=s.toneMapping);const Ne={shaderID:me,shaderType:C.type,shaderName:C.name,vertexShader:Z,fragmentShader:ue,defines:C.defines,customVertexShaderID:he,customFragmentShaderID:K,isRawShaderMaterial:C.isRawShaderMaterial===!0,glslVersion:C.glslVersion,precision:S,batching:we,batchingColor:we&&ee._colorsTexture!==null,instancing:ye,instancingColor:ye&&ee.instanceColor!==null,instancingMorph:ye&&ee.morphTexture!==null,supportsVertexTextures:_,outputColorSpace:oe===null?s.outputColorSpace:oe.isXRRenderTarget===!0?oe.texture.colorSpace:to,alphaToCoverage:!!C.alphaToCoverage,map:tt,matcap:at,envMap:U,envMapMode:U&&re.mapping,envMapCubeUVHeight:V,aoMap:Me,lightMap:_e,bumpMap:Se,normalMap:fe,displacementMap:_&&be,emissiveMap:xe,normalMapObjectSpace:fe&&C.normalMapType===Tx,normalMapTangentSpace:fe&&C.normalMapType===X0,metalnessMap:Re,roughnessMap:ct,anisotropy:ft,anisotropyMap:ve,clearcoat:L,clearcoatMap:Je,clearcoatNormalMap:Le,clearcoatRoughnessMap:Ke,dispersion:w,iridescence:J,iridescenceMap:nt,iridescenceThicknessMap:Ie,sheen:ge,sheenColorMap:He,sheenRoughnessMap:ut,specularMap:Ze,specularColorMap:Ve,specularIntensityMap:ht,transmission:Ae,transmissionMap:X,thicknessMap:Ue,gradientMap:ke,opaque:C.transparent===!1&&C.blending===Ks&&C.alphaToCoverage===!1,alphaMap:Xe,alphaTest:De,alphaHash:Te,combine:C.combine,mapUv:tt&&A(C.map.channel),aoMapUv:Me&&A(C.aoMap.channel),lightMapUv:_e&&A(C.lightMap.channel),bumpMapUv:Se&&A(C.bumpMap.channel),normalMapUv:fe&&A(C.normalMap.channel),displacementMapUv:be&&A(C.displacementMap.channel),emissiveMapUv:xe&&A(C.emissiveMap.channel),metalnessMapUv:Re&&A(C.metalnessMap.channel),roughnessMapUv:ct&&A(C.roughnessMap.channel),anisotropyMapUv:ve&&A(C.anisotropyMap.channel),clearcoatMapUv:Je&&A(C.clearcoatMap.channel),clearcoatNormalMapUv:Le&&A(C.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:Ke&&A(C.clearcoatRoughnessMap.channel),iridescenceMapUv:nt&&A(C.iridescenceMap.channel),iridescenceThicknessMapUv:Ie&&A(C.iridescenceThicknessMap.channel),sheenColorMapUv:He&&A(C.sheenColorMap.channel),sheenRoughnessMapUv:ut&&A(C.sheenRoughnessMap.channel),specularMapUv:Ze&&A(C.specularMap.channel),specularColorMapUv:Ve&&A(C.specularColorMap.channel),specularIntensityMapUv:ht&&A(C.specularIntensityMap.channel),transmissionMapUv:X&&A(C.transmissionMap.channel),thicknessMapUv:Ue&&A(C.thicknessMap.channel),alphaMapUv:Xe&&A(C.alphaMap.channel),vertexTangents:!!ne.attributes.tangent&&(fe||ft),vertexColors:C.vertexColors,vertexAlphas:C.vertexColors===!0&&!!ne.attributes.color&&ne.attributes.color.itemSize===4,pointsUvs:ee.isPoints===!0&&!!ne.attributes.uv&&(tt||Xe),fog:!!le,useFog:C.fog===!0,fogExp2:!!le&&le.isFogExp2,flatShading:C.flatShading===!0&&C.wireframe===!1,sizeAttenuation:C.sizeAttenuation===!0,logarithmicDepthBuffer:g,reversedDepthBuffer:Ee,skinning:ee.isSkinnedMesh===!0,morphTargets:ne.morphAttributes.position!==void 0,morphNormals:ne.morphAttributes.normal!==void 0,morphColors:ne.morphAttributes.color!==void 0,morphTargetsCount:P,morphTextureStride:B,numDirLights:T.directional.length,numPointLights:T.point.length,numSpotLights:T.spot.length,numSpotLightMaps:T.spotLightMap.length,numRectAreaLights:T.rectArea.length,numHemiLights:T.hemi.length,numDirLightShadows:T.directionalShadowMap.length,numPointLightShadows:T.pointShadowMap.length,numSpotLightShadows:T.spotShadowMap.length,numSpotLightShadowsWithMaps:T.numSpotLightShadowsWithMaps,numLightProbes:T.numLightProbes,numClippingPlanes:u.numPlanes,numClipIntersection:u.numIntersection,dithering:C.dithering,shadowMapEnabled:s.shadowMap.enabled&&F.length>0,shadowMapType:s.shadowMap.type,toneMapping:xt,decodeVideoTexture:tt&&C.map.isVideoTexture===!0&&Nt.getTransfer(C.map.colorSpace)===kt,decodeVideoTextureEmissive:xe&&C.emissiveMap.isVideoTexture===!0&&Nt.getTransfer(C.emissiveMap.colorSpace)===kt,premultipliedAlpha:C.premultipliedAlpha,doubleSided:C.side===Wi,flipSided:C.side===Gn,useDepthPacking:C.depthPacking>=0,depthPacking:C.depthPacking||0,index0AttributeName:C.index0AttributeName,extensionClipCullDistance:et&&C.extensions.clipCullDistance===!0&&r.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(et&&C.extensions.multiDraw===!0||we)&&r.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:r.has("KHR_parallel_shader_compile"),customProgramCacheKey:C.customProgramCacheKey()};return Ne.vertexUv1s=p.has(1),Ne.vertexUv2s=p.has(2),Ne.vertexUv3s=p.has(3),p.clear(),Ne}function x(C){const T=[];if(C.shaderID?T.push(C.shaderID):(T.push(C.customVertexShaderID),T.push(C.customFragmentShaderID)),C.defines!==void 0)for(const F in C.defines)T.push(F),T.push(C.defines[F]);return C.isRawShaderMaterial===!1&&(O(T,C),D(T,C),T.push(s.outputColorSpace)),T.push(C.customProgramCacheKey),T.join()}function O(C,T){C.push(T.precision),C.push(T.outputColorSpace),C.push(T.envMapMode),C.push(T.envMapCubeUVHeight),C.push(T.mapUv),C.push(T.alphaMapUv),C.push(T.lightMapUv),C.push(T.aoMapUv),C.push(T.bumpMapUv),C.push(T.normalMapUv),C.push(T.displacementMapUv),C.push(T.emissiveMapUv),C.push(T.metalnessMapUv),C.push(T.roughnessMapUv),C.push(T.anisotropyMapUv),C.push(T.clearcoatMapUv),C.push(T.clearcoatNormalMapUv),C.push(T.clearcoatRoughnessMapUv),C.push(T.iridescenceMapUv),C.push(T.iridescenceThicknessMapUv),C.push(T.sheenColorMapUv),C.push(T.sheenRoughnessMapUv),C.push(T.specularMapUv),C.push(T.specularColorMapUv),C.push(T.specularIntensityMapUv),C.push(T.transmissionMapUv),C.push(T.thicknessMapUv),C.push(T.combine),C.push(T.fogExp2),C.push(T.sizeAttenuation),C.push(T.morphTargetsCount),C.push(T.morphAttributeCount),C.push(T.numDirLights),C.push(T.numPointLights),C.push(T.numSpotLights),C.push(T.numSpotLightMaps),C.push(T.numHemiLights),C.push(T.numRectAreaLights),C.push(T.numDirLightShadows),C.push(T.numPointLightShadows),C.push(T.numSpotLightShadows),C.push(T.numSpotLightShadowsWithMaps),C.push(T.numLightProbes),C.push(T.shadowMapType),C.push(T.toneMapping),C.push(T.numClippingPlanes),C.push(T.numClipIntersection),C.push(T.depthPacking)}function D(C,T){f.disableAll(),T.supportsVertexTextures&&f.enable(0),T.instancing&&f.enable(1),T.instancingColor&&f.enable(2),T.instancingMorph&&f.enable(3),T.matcap&&f.enable(4),T.envMap&&f.enable(5),T.normalMapObjectSpace&&f.enable(6),T.normalMapTangentSpace&&f.enable(7),T.clearcoat&&f.enable(8),T.iridescence&&f.enable(9),T.alphaTest&&f.enable(10),T.vertexColors&&f.enable(11),T.vertexAlphas&&f.enable(12),T.vertexUv1s&&f.enable(13),T.vertexUv2s&&f.enable(14),T.vertexUv3s&&f.enable(15),T.vertexTangents&&f.enable(16),T.anisotropy&&f.enable(17),T.alphaHash&&f.enable(18),T.batching&&f.enable(19),T.dispersion&&f.enable(20),T.batchingColor&&f.enable(21),T.gradientMap&&f.enable(22),C.push(f.mask),f.disableAll(),T.fog&&f.enable(0),T.useFog&&f.enable(1),T.flatShading&&f.enable(2),T.logarithmicDepthBuffer&&f.enable(3),T.reversedDepthBuffer&&f.enable(4),T.skinning&&f.enable(5),T.morphTargets&&f.enable(6),T.morphNormals&&f.enable(7),T.morphColors&&f.enable(8),T.premultipliedAlpha&&f.enable(9),T.shadowMapEnabled&&f.enable(10),T.doubleSided&&f.enable(11),T.flipSided&&f.enable(12),T.useDepthPacking&&f.enable(13),T.dithering&&f.enable(14),T.transmission&&f.enable(15),T.sheen&&f.enable(16),T.opaque&&f.enable(17),T.pointsUvs&&f.enable(18),T.decodeVideoTexture&&f.enable(19),T.decodeVideoTextureEmissive&&f.enable(20),T.alphaToCoverage&&f.enable(21),C.push(f.mask)}function R(C){const T=M[C.type];let F;if(T){const $=Mi[T];F=ey.clone($.uniforms)}else F=C.uniforms;return F}function z(C,T){let F;for(let $=0,ee=v.length;$<ee;$++){const le=v[$];if(le.cacheKey===T){F=le,++F.usedTimes;break}}return F===void 0&&(F=new ow(s,T,C,l),v.push(F)),F}function H(C){if(--C.usedTimes===0){const T=v.indexOf(C);v[T]=v[v.length-1],v.pop(),C.destroy()}}function I(C){d.remove(C)}function N(){d.dispose()}return{getParameters:y,getProgramCacheKey:x,getUniforms:R,acquireProgram:z,releaseProgram:H,releaseShaderCache:I,programs:v,dispose:N}}function fw(){let s=new WeakMap;function e(u){return s.has(u)}function t(u){let f=s.get(u);return f===void 0&&(f={},s.set(u,f)),f}function r(u){s.delete(u)}function o(u,f,d){s.get(u)[f]=d}function l(){s=new WeakMap}return{has:e,get:t,remove:r,update:o,dispose:l}}function dw(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.material.id!==e.material.id?s.material.id-e.material.id:s.z!==e.z?s.z-e.z:s.id-e.id}function x0(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.z!==e.z?e.z-s.z:s.id-e.id}function y0(){const s=[];let e=0;const t=[],r=[],o=[];function l(){e=0,t.length=0,r.length=0,o.length=0}function u(g,_,S,M,A,y){let x=s[e];return x===void 0?(x={id:g.id,object:g,geometry:_,material:S,groupOrder:M,renderOrder:g.renderOrder,z:A,group:y},s[e]=x):(x.id=g.id,x.object=g,x.geometry=_,x.material=S,x.groupOrder=M,x.renderOrder=g.renderOrder,x.z=A,x.group=y),e++,x}function f(g,_,S,M,A,y){const x=u(g,_,S,M,A,y);S.transmission>0?r.push(x):S.transparent===!0?o.push(x):t.push(x)}function d(g,_,S,M,A,y){const x=u(g,_,S,M,A,y);S.transmission>0?r.unshift(x):S.transparent===!0?o.unshift(x):t.unshift(x)}function p(g,_){t.length>1&&t.sort(g||dw),r.length>1&&r.sort(_||x0),o.length>1&&o.sort(_||x0)}function v(){for(let g=e,_=s.length;g<_;g++){const S=s[g];if(S.id===null)break;S.id=null,S.object=null,S.geometry=null,S.material=null,S.group=null}}return{opaque:t,transmissive:r,transparent:o,init:l,push:f,unshift:d,finish:v,sort:p}}function hw(){let s=new WeakMap;function e(r,o){const l=s.get(r);let u;return l===void 0?(u=new y0,s.set(r,[u])):o>=l.length?(u=new y0,l.push(u)):u=l[o],u}function t(){s=new WeakMap}return{get:e,dispose:t}}function pw(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new Q,color:new It};break;case"SpotLight":t={position:new Q,direction:new Q,color:new It,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new Q,color:new It,distance:0,decay:0};break;case"HemisphereLight":t={direction:new Q,skyColor:new It,groundColor:new It};break;case"RectAreaLight":t={color:new It,position:new Q,halfWidth:new Q,halfHeight:new Q};break}return s[e.id]=t,t}}}function mw(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ge};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ge};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ge,shadowCameraNear:1,shadowCameraFar:1e3};break}return s[e.id]=t,t}}}let gw=0;function vw(s,e){return(e.castShadow?2:0)-(s.castShadow?2:0)+(e.map?1:0)-(s.map?1:0)}function _w(s){const e=new pw,t=mw(),r={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let p=0;p<9;p++)r.probe.push(new Q);const o=new Q,l=new $t,u=new $t;function f(p){let v=0,g=0,_=0;for(let C=0;C<9;C++)r.probe[C].set(0,0,0);let S=0,M=0,A=0,y=0,x=0,O=0,D=0,R=0,z=0,H=0,I=0;p.sort(vw);for(let C=0,T=p.length;C<T;C++){const F=p[C],$=F.color,ee=F.intensity,le=F.distance,ne=F.shadow&&F.shadow.map?F.shadow.map.texture:null;if(F.isAmbientLight)v+=$.r*ee,g+=$.g*ee,_+=$.b*ee;else if(F.isLightProbe){for(let ce=0;ce<9;ce++)r.probe[ce].addScaledVector(F.sh.coefficients[ce],ee);I++}else if(F.isDirectionalLight){const ce=e.get(F);if(ce.color.copy(F.color).multiplyScalar(F.intensity),F.castShadow){const re=F.shadow,V=t.get(F);V.shadowIntensity=re.intensity,V.shadowBias=re.bias,V.shadowNormalBias=re.normalBias,V.shadowRadius=re.radius,V.shadowMapSize=re.mapSize,r.directionalShadow[S]=V,r.directionalShadowMap[S]=ne,r.directionalShadowMatrix[S]=F.shadow.matrix,O++}r.directional[S]=ce,S++}else if(F.isSpotLight){const ce=e.get(F);ce.position.setFromMatrixPosition(F.matrixWorld),ce.color.copy($).multiplyScalar(ee),ce.distance=le,ce.coneCos=Math.cos(F.angle),ce.penumbraCos=Math.cos(F.angle*(1-F.penumbra)),ce.decay=F.decay,r.spot[A]=ce;const re=F.shadow;if(F.map&&(r.spotLightMap[z]=F.map,z++,re.updateMatrices(F),F.castShadow&&H++),r.spotLightMatrix[A]=re.matrix,F.castShadow){const V=t.get(F);V.shadowIntensity=re.intensity,V.shadowBias=re.bias,V.shadowNormalBias=re.normalBias,V.shadowRadius=re.radius,V.shadowMapSize=re.mapSize,r.spotShadow[A]=V,r.spotShadowMap[A]=ne,R++}A++}else if(F.isRectAreaLight){const ce=e.get(F);ce.color.copy($).multiplyScalar(ee),ce.halfWidth.set(F.width*.5,0,0),ce.halfHeight.set(0,F.height*.5,0),r.rectArea[y]=ce,y++}else if(F.isPointLight){const ce=e.get(F);if(ce.color.copy(F.color).multiplyScalar(F.intensity),ce.distance=F.distance,ce.decay=F.decay,F.castShadow){const re=F.shadow,V=t.get(F);V.shadowIntensity=re.intensity,V.shadowBias=re.bias,V.shadowNormalBias=re.normalBias,V.shadowRadius=re.radius,V.shadowMapSize=re.mapSize,V.shadowCameraNear=re.camera.near,V.shadowCameraFar=re.camera.far,r.pointShadow[M]=V,r.pointShadowMap[M]=ne,r.pointShadowMatrix[M]=F.shadow.matrix,D++}r.point[M]=ce,M++}else if(F.isHemisphereLight){const ce=e.get(F);ce.skyColor.copy(F.color).multiplyScalar(ee),ce.groundColor.copy(F.groundColor).multiplyScalar(ee),r.hemi[x]=ce,x++}}y>0&&(s.has("OES_texture_float_linear")===!0?(r.rectAreaLTC1=je.LTC_FLOAT_1,r.rectAreaLTC2=je.LTC_FLOAT_2):(r.rectAreaLTC1=je.LTC_HALF_1,r.rectAreaLTC2=je.LTC_HALF_2)),r.ambient[0]=v,r.ambient[1]=g,r.ambient[2]=_;const N=r.hash;(N.directionalLength!==S||N.pointLength!==M||N.spotLength!==A||N.rectAreaLength!==y||N.hemiLength!==x||N.numDirectionalShadows!==O||N.numPointShadows!==D||N.numSpotShadows!==R||N.numSpotMaps!==z||N.numLightProbes!==I)&&(r.directional.length=S,r.spot.length=A,r.rectArea.length=y,r.point.length=M,r.hemi.length=x,r.directionalShadow.length=O,r.directionalShadowMap.length=O,r.pointShadow.length=D,r.pointShadowMap.length=D,r.spotShadow.length=R,r.spotShadowMap.length=R,r.directionalShadowMatrix.length=O,r.pointShadowMatrix.length=D,r.spotLightMatrix.length=R+z-H,r.spotLightMap.length=z,r.numSpotLightShadowsWithMaps=H,r.numLightProbes=I,N.directionalLength=S,N.pointLength=M,N.spotLength=A,N.rectAreaLength=y,N.hemiLength=x,N.numDirectionalShadows=O,N.numPointShadows=D,N.numSpotShadows=R,N.numSpotMaps=z,N.numLightProbes=I,r.version=gw++)}function d(p,v){let g=0,_=0,S=0,M=0,A=0;const y=v.matrixWorldInverse;for(let x=0,O=p.length;x<O;x++){const D=p[x];if(D.isDirectionalLight){const R=r.directional[g];R.direction.setFromMatrixPosition(D.matrixWorld),o.setFromMatrixPosition(D.target.matrixWorld),R.direction.sub(o),R.direction.transformDirection(y),g++}else if(D.isSpotLight){const R=r.spot[S];R.position.setFromMatrixPosition(D.matrixWorld),R.position.applyMatrix4(y),R.direction.setFromMatrixPosition(D.matrixWorld),o.setFromMatrixPosition(D.target.matrixWorld),R.direction.sub(o),R.direction.transformDirection(y),S++}else if(D.isRectAreaLight){const R=r.rectArea[M];R.position.setFromMatrixPosition(D.matrixWorld),R.position.applyMatrix4(y),u.identity(),l.copy(D.matrixWorld),l.premultiply(y),u.extractRotation(l),R.halfWidth.set(D.width*.5,0,0),R.halfHeight.set(0,D.height*.5,0),R.halfWidth.applyMatrix4(u),R.halfHeight.applyMatrix4(u),M++}else if(D.isPointLight){const R=r.point[_];R.position.setFromMatrixPosition(D.matrixWorld),R.position.applyMatrix4(y),_++}else if(D.isHemisphereLight){const R=r.hemi[A];R.direction.setFromMatrixPosition(D.matrixWorld),R.direction.transformDirection(y),A++}}}return{setup:f,setupView:d,state:r}}function S0(s){const e=new _w(s),t=[],r=[];function o(v){p.camera=v,t.length=0,r.length=0}function l(v){t.push(v)}function u(v){r.push(v)}function f(){e.setup(t)}function d(v){e.setupView(t,v)}const p={lightsArray:t,shadowsArray:r,camera:null,lights:e,transmissionRenderTarget:{}};return{init:o,state:p,setupLights:f,setupLightsView:d,pushLight:l,pushShadow:u}}function xw(s){let e=new WeakMap;function t(o,l=0){const u=e.get(o);let f;return u===void 0?(f=new S0(s),e.set(o,[f])):l>=u.length?(f=new S0(s),u.push(f)):f=u[l],f}function r(){e=new WeakMap}return{get:t,dispose:r}}const yw=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,Sw=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;function Mw(s,e,t){let r=new Cd;const o=new Ge,l=new Ge,u=new Zt,f=new Xy({depthPacking:wx}),d=new jy,p={},v=t.maxTextureSize,g={[Cr]:Gn,[Gn]:Cr,[Wi]:Wi},_=new br({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Ge},radius:{value:4}},vertexShader:yw,fragmentShader:Sw}),S=_.clone();S.defines.HORIZONTAL_PASS=1;const M=new Ci;M.setAttribute("position",new Ti(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const A=new an(M,_),y=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=I0;let x=this.type;this.render=function(H,I,N){if(y.enabled===!1||y.autoUpdate===!1&&y.needsUpdate===!1||H.length===0)return;const C=s.getRenderTarget(),T=s.getActiveCubeFace(),F=s.getActiveMipmapLevel(),$=s.state;$.setBlending(Ar),$.buffers.depth.getReversed()===!0?$.buffers.color.setClear(0,0,0,0):$.buffers.color.setClear(1,1,1,1),$.buffers.depth.setTest(!0),$.setScissorTest(!1);const ee=x!==Gi&&this.type===Gi,le=x===Gi&&this.type!==Gi;for(let ne=0,ce=H.length;ne<ce;ne++){const re=H[ne],V=re.shadow;if(V===void 0){console.warn("THREE.WebGLShadowMap:",re,"has no shadow.");continue}if(V.autoUpdate===!1&&V.needsUpdate===!1)continue;o.copy(V.mapSize);const me=V.getFrameExtents();if(o.multiply(me),l.copy(V.mapSize),(o.x>v||o.y>v)&&(o.x>v&&(l.x=Math.floor(v/me.x),o.x=l.x*me.x,V.mapSize.x=l.x),o.y>v&&(l.y=Math.floor(v/me.y),o.y=l.y*me.y,V.mapSize.y=l.y)),V.map===null||ee===!0||le===!0){const P=this.type!==Gi?{minFilter:vi,magFilter:vi}:{};V.map!==null&&V.map.dispose(),V.map=new os(o.x,o.y,P),V.map.texture.name=re.name+".shadowMap",V.camera.updateProjectionMatrix()}s.setRenderTarget(V.map),s.clear();const ie=V.getViewportCount();for(let P=0;P<ie;P++){const B=V.getViewport(P);u.set(l.x*B.x,l.y*B.y,l.x*B.z,l.y*B.w),$.viewport(u),V.updateMatrices(re,P),r=V.getFrustum(),R(I,N,V.camera,re,this.type)}V.isPointLightShadow!==!0&&this.type===Gi&&O(V,N),V.needsUpdate=!1}x=this.type,y.needsUpdate=!1,s.setRenderTarget(C,T,F)};function O(H,I){const N=e.update(A);_.defines.VSM_SAMPLES!==H.blurSamples&&(_.defines.VSM_SAMPLES=H.blurSamples,S.defines.VSM_SAMPLES=H.blurSamples,_.needsUpdate=!0,S.needsUpdate=!0),H.mapPass===null&&(H.mapPass=new os(o.x,o.y)),_.uniforms.shadow_pass.value=H.map.texture,_.uniforms.resolution.value=H.mapSize,_.uniforms.radius.value=H.radius,s.setRenderTarget(H.mapPass),s.clear(),s.renderBufferDirect(I,null,N,_,A,null),S.uniforms.shadow_pass.value=H.mapPass.texture,S.uniforms.resolution.value=H.mapSize,S.uniforms.radius.value=H.radius,s.setRenderTarget(H.map),s.clear(),s.renderBufferDirect(I,null,N,S,A,null)}function D(H,I,N,C){let T=null;const F=N.isPointLight===!0?H.customDistanceMaterial:H.customDepthMaterial;if(F!==void 0)T=F;else if(T=N.isPointLight===!0?d:f,s.localClippingEnabled&&I.clipShadows===!0&&Array.isArray(I.clippingPlanes)&&I.clippingPlanes.length!==0||I.displacementMap&&I.displacementScale!==0||I.alphaMap&&I.alphaTest>0||I.map&&I.alphaTest>0||I.alphaToCoverage===!0){const $=T.uuid,ee=I.uuid;let le=p[$];le===void 0&&(le={},p[$]=le);let ne=le[ee];ne===void 0&&(ne=T.clone(),le[ee]=ne,I.addEventListener("dispose",z)),T=ne}if(T.visible=I.visible,T.wireframe=I.wireframe,C===Gi?T.side=I.shadowSide!==null?I.shadowSide:I.side:T.side=I.shadowSide!==null?I.shadowSide:g[I.side],T.alphaMap=I.alphaMap,T.alphaTest=I.alphaToCoverage===!0?.5:I.alphaTest,T.map=I.map,T.clipShadows=I.clipShadows,T.clippingPlanes=I.clippingPlanes,T.clipIntersection=I.clipIntersection,T.displacementMap=I.displacementMap,T.displacementScale=I.displacementScale,T.displacementBias=I.displacementBias,T.wireframeLinewidth=I.wireframeLinewidth,T.linewidth=I.linewidth,N.isPointLight===!0&&T.isMeshDistanceMaterial===!0){const $=s.properties.get(T);$.light=N}return T}function R(H,I,N,C,T){if(H.visible===!1)return;if(H.layers.test(I.layers)&&(H.isMesh||H.isLine||H.isPoints)&&(H.castShadow||H.receiveShadow&&T===Gi)&&(!H.frustumCulled||r.intersectsObject(H))){H.modelViewMatrix.multiplyMatrices(N.matrixWorldInverse,H.matrixWorld);const ee=e.update(H),le=H.material;if(Array.isArray(le)){const ne=ee.groups;for(let ce=0,re=ne.length;ce<re;ce++){const V=ne[ce],me=le[V.materialIndex];if(me&&me.visible){const ie=D(H,me,C,T);H.onBeforeShadow(s,H,I,N,ee,ie,V),s.renderBufferDirect(N,null,ee,ie,H,V),H.onAfterShadow(s,H,I,N,ee,ie,V)}}}else if(le.visible){const ne=D(H,le,C,T);H.onBeforeShadow(s,H,I,N,ee,ne,null),s.renderBufferDirect(N,null,ee,ne,H,null),H.onAfterShadow(s,H,I,N,ee,ne,null)}}const $=H.children;for(let ee=0,le=$.length;ee<le;ee++)R($[ee],I,N,C,T)}function z(H){H.target.removeEventListener("dispose",z);for(const N in p){const C=p[N],T=H.target.uuid;T in C&&(C[T].dispose(),delete C[T])}}}const Ew={[wf]:Tf,[Af]:bf,[Rf]:Pf,[Js]:Cf,[Tf]:wf,[bf]:Af,[Pf]:Rf,[Cf]:Js};function ww(s,e){function t(){let X=!1;const Ue=new Zt;let ke=null;const Xe=new Zt(0,0,0,0);return{setMask:function(De){ke!==De&&!X&&(s.colorMask(De,De,De,De),ke=De)},setLocked:function(De){X=De},setClear:function(De,Te,et,xt,Ne){Ne===!0&&(De*=xt,Te*=xt,et*=xt),Ue.set(De,Te,et,xt),Xe.equals(Ue)===!1&&(s.clearColor(De,Te,et,xt),Xe.copy(Ue))},reset:function(){X=!1,ke=null,Xe.set(-1,0,0,0)}}}function r(){let X=!1,Ue=!1,ke=null,Xe=null,De=null;return{setReversed:function(Te){if(Ue!==Te){const et=e.get("EXT_clip_control");Te?et.clipControlEXT(et.LOWER_LEFT_EXT,et.ZERO_TO_ONE_EXT):et.clipControlEXT(et.LOWER_LEFT_EXT,et.NEGATIVE_ONE_TO_ONE_EXT),Ue=Te;const xt=De;De=null,this.setClear(xt)}},getReversed:function(){return Ue},setTest:function(Te){Te?oe(s.DEPTH_TEST):Ee(s.DEPTH_TEST)},setMask:function(Te){ke!==Te&&!X&&(s.depthMask(Te),ke=Te)},setFunc:function(Te){if(Ue&&(Te=Ew[Te]),Xe!==Te){switch(Te){case wf:s.depthFunc(s.NEVER);break;case Tf:s.depthFunc(s.ALWAYS);break;case Af:s.depthFunc(s.LESS);break;case Js:s.depthFunc(s.LEQUAL);break;case Rf:s.depthFunc(s.EQUAL);break;case Cf:s.depthFunc(s.GEQUAL);break;case bf:s.depthFunc(s.GREATER);break;case Pf:s.depthFunc(s.NOTEQUAL);break;default:s.depthFunc(s.LEQUAL)}Xe=Te}},setLocked:function(Te){X=Te},setClear:function(Te){De!==Te&&(Ue&&(Te=1-Te),s.clearDepth(Te),De=Te)},reset:function(){X=!1,ke=null,Xe=null,De=null,Ue=!1}}}function o(){let X=!1,Ue=null,ke=null,Xe=null,De=null,Te=null,et=null,xt=null,Ne=null;return{setTest:function(qe){X||(qe?oe(s.STENCIL_TEST):Ee(s.STENCIL_TEST))},setMask:function(qe){Ue!==qe&&!X&&(s.stencilMask(qe),Ue=qe)},setFunc:function(qe,Mt,vt){(ke!==qe||Xe!==Mt||De!==vt)&&(s.stencilFunc(qe,Mt,vt),ke=qe,Xe=Mt,De=vt)},setOp:function(qe,Mt,vt){(Te!==qe||et!==Mt||xt!==vt)&&(s.stencilOp(qe,Mt,vt),Te=qe,et=Mt,xt=vt)},setLocked:function(qe){X=qe},setClear:function(qe){Ne!==qe&&(s.clearStencil(qe),Ne=qe)},reset:function(){X=!1,Ue=null,ke=null,Xe=null,De=null,Te=null,et=null,xt=null,Ne=null}}}const l=new t,u=new r,f=new o,d=new WeakMap,p=new WeakMap;let v={},g={},_=new WeakMap,S=[],M=null,A=!1,y=null,x=null,O=null,D=null,R=null,z=null,H=null,I=new It(0,0,0),N=0,C=!1,T=null,F=null,$=null,ee=null,le=null;const ne=s.getParameter(s.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let ce=!1,re=0;const V=s.getParameter(s.VERSION);V.indexOf("WebGL")!==-1?(re=parseFloat(/^WebGL (\d)/.exec(V)[1]),ce=re>=1):V.indexOf("OpenGL ES")!==-1&&(re=parseFloat(/^OpenGL ES (\d)/.exec(V)[1]),ce=re>=2);let me=null,ie={};const P=s.getParameter(s.SCISSOR_BOX),B=s.getParameter(s.VIEWPORT),Z=new Zt().fromArray(P),ue=new Zt().fromArray(B);function he(X,Ue,ke,Xe){const De=new Uint8Array(4),Te=s.createTexture();s.bindTexture(X,Te),s.texParameteri(X,s.TEXTURE_MIN_FILTER,s.NEAREST),s.texParameteri(X,s.TEXTURE_MAG_FILTER,s.NEAREST);for(let et=0;et<ke;et++)X===s.TEXTURE_3D||X===s.TEXTURE_2D_ARRAY?s.texImage3D(Ue,0,s.RGBA,1,1,Xe,0,s.RGBA,s.UNSIGNED_BYTE,De):s.texImage2D(Ue+et,0,s.RGBA,1,1,0,s.RGBA,s.UNSIGNED_BYTE,De);return Te}const K={};K[s.TEXTURE_2D]=he(s.TEXTURE_2D,s.TEXTURE_2D,1),K[s.TEXTURE_CUBE_MAP]=he(s.TEXTURE_CUBE_MAP,s.TEXTURE_CUBE_MAP_POSITIVE_X,6),K[s.TEXTURE_2D_ARRAY]=he(s.TEXTURE_2D_ARRAY,s.TEXTURE_2D_ARRAY,1,1),K[s.TEXTURE_3D]=he(s.TEXTURE_3D,s.TEXTURE_3D,1,1),l.setClear(0,0,0,1),u.setClear(1),f.setClear(0),oe(s.DEPTH_TEST),u.setFunc(Js),Se(!1),fe(vm),oe(s.CULL_FACE),Me(Ar);function oe(X){v[X]!==!0&&(s.enable(X),v[X]=!0)}function Ee(X){v[X]!==!1&&(s.disable(X),v[X]=!1)}function ye(X,Ue){return g[X]!==Ue?(s.bindFramebuffer(X,Ue),g[X]=Ue,X===s.DRAW_FRAMEBUFFER&&(g[s.FRAMEBUFFER]=Ue),X===s.FRAMEBUFFER&&(g[s.DRAW_FRAMEBUFFER]=Ue),!0):!1}function we(X,Ue){let ke=S,Xe=!1;if(X){ke=_.get(Ue),ke===void 0&&(ke=[],_.set(Ue,ke));const De=X.textures;if(ke.length!==De.length||ke[0]!==s.COLOR_ATTACHMENT0){for(let Te=0,et=De.length;Te<et;Te++)ke[Te]=s.COLOR_ATTACHMENT0+Te;ke.length=De.length,Xe=!0}}else ke[0]!==s.BACK&&(ke[0]=s.BACK,Xe=!0);Xe&&s.drawBuffers(ke)}function tt(X){return M!==X?(s.useProgram(X),M=X,!0):!1}const at={[ts]:s.FUNC_ADD,[K_]:s.FUNC_SUBTRACT,[Z_]:s.FUNC_REVERSE_SUBTRACT};at[J_]=s.MIN,at[Q_]=s.MAX;const U={[ex]:s.ZERO,[tx]:s.ONE,[nx]:s.SRC_COLOR,[Mf]:s.SRC_ALPHA,[lx]:s.SRC_ALPHA_SATURATE,[ox]:s.DST_COLOR,[rx]:s.DST_ALPHA,[ix]:s.ONE_MINUS_SRC_COLOR,[Ef]:s.ONE_MINUS_SRC_ALPHA,[ax]:s.ONE_MINUS_DST_COLOR,[sx]:s.ONE_MINUS_DST_ALPHA,[cx]:s.CONSTANT_COLOR,[ux]:s.ONE_MINUS_CONSTANT_COLOR,[fx]:s.CONSTANT_ALPHA,[dx]:s.ONE_MINUS_CONSTANT_ALPHA};function Me(X,Ue,ke,Xe,De,Te,et,xt,Ne,qe){if(X===Ar){A===!0&&(Ee(s.BLEND),A=!1);return}if(A===!1&&(oe(s.BLEND),A=!0),X!==$_){if(X!==y||qe!==C){if((x!==ts||R!==ts)&&(s.blendEquation(s.FUNC_ADD),x=ts,R=ts),qe)switch(X){case Ks:s.blendFuncSeparate(s.ONE,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case _m:s.blendFunc(s.ONE,s.ONE);break;case xm:s.blendFuncSeparate(s.ZERO,s.ONE_MINUS_SRC_COLOR,s.ZERO,s.ONE);break;case ym:s.blendFuncSeparate(s.DST_COLOR,s.ONE_MINUS_SRC_ALPHA,s.ZERO,s.ONE);break;default:console.error("THREE.WebGLState: Invalid blending: ",X);break}else switch(X){case Ks:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case _m:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE,s.ONE,s.ONE);break;case xm:console.error("THREE.WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case ym:console.error("THREE.WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:console.error("THREE.WebGLState: Invalid blending: ",X);break}O=null,D=null,z=null,H=null,I.set(0,0,0),N=0,y=X,C=qe}return}De=De||Ue,Te=Te||ke,et=et||Xe,(Ue!==x||De!==R)&&(s.blendEquationSeparate(at[Ue],at[De]),x=Ue,R=De),(ke!==O||Xe!==D||Te!==z||et!==H)&&(s.blendFuncSeparate(U[ke],U[Xe],U[Te],U[et]),O=ke,D=Xe,z=Te,H=et),(xt.equals(I)===!1||Ne!==N)&&(s.blendColor(xt.r,xt.g,xt.b,Ne),I.copy(xt),N=Ne),y=X,C=!1}function _e(X,Ue){X.side===Wi?Ee(s.CULL_FACE):oe(s.CULL_FACE);let ke=X.side===Gn;Ue&&(ke=!ke),Se(ke),X.blending===Ks&&X.transparent===!1?Me(Ar):Me(X.blending,X.blendEquation,X.blendSrc,X.blendDst,X.blendEquationAlpha,X.blendSrcAlpha,X.blendDstAlpha,X.blendColor,X.blendAlpha,X.premultipliedAlpha),u.setFunc(X.depthFunc),u.setTest(X.depthTest),u.setMask(X.depthWrite),l.setMask(X.colorWrite);const Xe=X.stencilWrite;f.setTest(Xe),Xe&&(f.setMask(X.stencilWriteMask),f.setFunc(X.stencilFunc,X.stencilRef,X.stencilFuncMask),f.setOp(X.stencilFail,X.stencilZFail,X.stencilZPass)),xe(X.polygonOffset,X.polygonOffsetFactor,X.polygonOffsetUnits),X.alphaToCoverage===!0?oe(s.SAMPLE_ALPHA_TO_COVERAGE):Ee(s.SAMPLE_ALPHA_TO_COVERAGE)}function Se(X){T!==X&&(X?s.frontFace(s.CW):s.frontFace(s.CCW),T=X)}function fe(X){X!==j_?(oe(s.CULL_FACE),X!==F&&(X===vm?s.cullFace(s.BACK):X===q_?s.cullFace(s.FRONT):s.cullFace(s.FRONT_AND_BACK))):Ee(s.CULL_FACE),F=X}function be(X){X!==$&&(ce&&s.lineWidth(X),$=X)}function xe(X,Ue,ke){X?(oe(s.POLYGON_OFFSET_FILL),(ee!==Ue||le!==ke)&&(s.polygonOffset(Ue,ke),ee=Ue,le=ke)):Ee(s.POLYGON_OFFSET_FILL)}function Re(X){X?oe(s.SCISSOR_TEST):Ee(s.SCISSOR_TEST)}function ct(X){X===void 0&&(X=s.TEXTURE0+ne-1),me!==X&&(s.activeTexture(X),me=X)}function ft(X,Ue,ke){ke===void 0&&(me===null?ke=s.TEXTURE0+ne-1:ke=me);let Xe=ie[ke];Xe===void 0&&(Xe={type:void 0,texture:void 0},ie[ke]=Xe),(Xe.type!==X||Xe.texture!==Ue)&&(me!==ke&&(s.activeTexture(ke),me=ke),s.bindTexture(X,Ue||K[X]),Xe.type=X,Xe.texture=Ue)}function L(){const X=ie[me];X!==void 0&&X.type!==void 0&&(s.bindTexture(X.type,null),X.type=void 0,X.texture=void 0)}function w(){try{s.compressedTexImage2D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function J(){try{s.compressedTexImage3D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function ge(){try{s.texSubImage2D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function Ae(){try{s.texSubImage3D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function ve(){try{s.compressedTexSubImage2D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function Je(){try{s.compressedTexSubImage3D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function Le(){try{s.texStorage2D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function Ke(){try{s.texStorage3D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function nt(){try{s.texImage2D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function Ie(){try{s.texImage3D(...arguments)}catch(X){console.error("THREE.WebGLState:",X)}}function He(X){Z.equals(X)===!1&&(s.scissor(X.x,X.y,X.z,X.w),Z.copy(X))}function ut(X){ue.equals(X)===!1&&(s.viewport(X.x,X.y,X.z,X.w),ue.copy(X))}function Ze(X,Ue){let ke=p.get(Ue);ke===void 0&&(ke=new WeakMap,p.set(Ue,ke));let Xe=ke.get(X);Xe===void 0&&(Xe=s.getUniformBlockIndex(Ue,X.name),ke.set(X,Xe))}function Ve(X,Ue){const Xe=p.get(Ue).get(X);d.get(Ue)!==Xe&&(s.uniformBlockBinding(Ue,Xe,X.__bindingPointIndex),d.set(Ue,Xe))}function ht(){s.disable(s.BLEND),s.disable(s.CULL_FACE),s.disable(s.DEPTH_TEST),s.disable(s.POLYGON_OFFSET_FILL),s.disable(s.SCISSOR_TEST),s.disable(s.STENCIL_TEST),s.disable(s.SAMPLE_ALPHA_TO_COVERAGE),s.blendEquation(s.FUNC_ADD),s.blendFunc(s.ONE,s.ZERO),s.blendFuncSeparate(s.ONE,s.ZERO,s.ONE,s.ZERO),s.blendColor(0,0,0,0),s.colorMask(!0,!0,!0,!0),s.clearColor(0,0,0,0),s.depthMask(!0),s.depthFunc(s.LESS),u.setReversed(!1),s.clearDepth(1),s.stencilMask(4294967295),s.stencilFunc(s.ALWAYS,0,4294967295),s.stencilOp(s.KEEP,s.KEEP,s.KEEP),s.clearStencil(0),s.cullFace(s.BACK),s.frontFace(s.CCW),s.polygonOffset(0,0),s.activeTexture(s.TEXTURE0),s.bindFramebuffer(s.FRAMEBUFFER,null),s.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),s.bindFramebuffer(s.READ_FRAMEBUFFER,null),s.useProgram(null),s.lineWidth(1),s.scissor(0,0,s.canvas.width,s.canvas.height),s.viewport(0,0,s.canvas.width,s.canvas.height),v={},me=null,ie={},g={},_=new WeakMap,S=[],M=null,A=!1,y=null,x=null,O=null,D=null,R=null,z=null,H=null,I=new It(0,0,0),N=0,C=!1,T=null,F=null,$=null,ee=null,le=null,Z.set(0,0,s.canvas.width,s.canvas.height),ue.set(0,0,s.canvas.width,s.canvas.height),l.reset(),u.reset(),f.reset()}return{buffers:{color:l,depth:u,stencil:f},enable:oe,disable:Ee,bindFramebuffer:ye,drawBuffers:we,useProgram:tt,setBlending:Me,setMaterial:_e,setFlipSided:Se,setCullFace:fe,setLineWidth:be,setPolygonOffset:xe,setScissorTest:Re,activeTexture:ct,bindTexture:ft,unbindTexture:L,compressedTexImage2D:w,compressedTexImage3D:J,texImage2D:nt,texImage3D:Ie,updateUBOMapping:Ze,uniformBlockBinding:Ve,texStorage2D:Le,texStorage3D:Ke,texSubImage2D:ge,texSubImage3D:Ae,compressedTexSubImage2D:ve,compressedTexSubImage3D:Je,scissor:He,viewport:ut,reset:ht}}function Tw(s,e,t,r,o,l,u){const f=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,d=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),p=new Ge,v=new WeakMap;let g;const _=new WeakMap;let S=!1;try{S=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function M(L,w){return S?new OffscreenCanvas(L,w):Zl("canvas")}function A(L,w,J){let ge=1;const Ae=ft(L);if((Ae.width>J||Ae.height>J)&&(ge=J/Math.max(Ae.width,Ae.height)),ge<1)if(typeof HTMLImageElement<"u"&&L instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&L instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&L instanceof ImageBitmap||typeof VideoFrame<"u"&&L instanceof VideoFrame){const ve=Math.floor(ge*Ae.width),Je=Math.floor(ge*Ae.height);g===void 0&&(g=M(ve,Je));const Le=w?M(ve,Je):g;return Le.width=ve,Le.height=Je,Le.getContext("2d").drawImage(L,0,0,ve,Je),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+Ae.width+"x"+Ae.height+") to ("+ve+"x"+Je+")."),Le}else return"data"in L&&console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+Ae.width+"x"+Ae.height+")."),L;return L}function y(L){return L.generateMipmaps}function x(L){s.generateMipmap(L)}function O(L){return L.isWebGLCubeRenderTarget?s.TEXTURE_CUBE_MAP:L.isWebGL3DRenderTarget?s.TEXTURE_3D:L.isWebGLArrayRenderTarget||L.isCompressedArrayTexture?s.TEXTURE_2D_ARRAY:s.TEXTURE_2D}function D(L,w,J,ge,Ae=!1){if(L!==null){if(s[L]!==void 0)return s[L];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+L+"'")}let ve=w;if(w===s.RED&&(J===s.FLOAT&&(ve=s.R32F),J===s.HALF_FLOAT&&(ve=s.R16F),J===s.UNSIGNED_BYTE&&(ve=s.R8)),w===s.RED_INTEGER&&(J===s.UNSIGNED_BYTE&&(ve=s.R8UI),J===s.UNSIGNED_SHORT&&(ve=s.R16UI),J===s.UNSIGNED_INT&&(ve=s.R32UI),J===s.BYTE&&(ve=s.R8I),J===s.SHORT&&(ve=s.R16I),J===s.INT&&(ve=s.R32I)),w===s.RG&&(J===s.FLOAT&&(ve=s.RG32F),J===s.HALF_FLOAT&&(ve=s.RG16F),J===s.UNSIGNED_BYTE&&(ve=s.RG8)),w===s.RG_INTEGER&&(J===s.UNSIGNED_BYTE&&(ve=s.RG8UI),J===s.UNSIGNED_SHORT&&(ve=s.RG16UI),J===s.UNSIGNED_INT&&(ve=s.RG32UI),J===s.BYTE&&(ve=s.RG8I),J===s.SHORT&&(ve=s.RG16I),J===s.INT&&(ve=s.RG32I)),w===s.RGB_INTEGER&&(J===s.UNSIGNED_BYTE&&(ve=s.RGB8UI),J===s.UNSIGNED_SHORT&&(ve=s.RGB16UI),J===s.UNSIGNED_INT&&(ve=s.RGB32UI),J===s.BYTE&&(ve=s.RGB8I),J===s.SHORT&&(ve=s.RGB16I),J===s.INT&&(ve=s.RGB32I)),w===s.RGBA_INTEGER&&(J===s.UNSIGNED_BYTE&&(ve=s.RGBA8UI),J===s.UNSIGNED_SHORT&&(ve=s.RGBA16UI),J===s.UNSIGNED_INT&&(ve=s.RGBA32UI),J===s.BYTE&&(ve=s.RGBA8I),J===s.SHORT&&(ve=s.RGBA16I),J===s.INT&&(ve=s.RGBA32I)),w===s.RGB&&(J===s.UNSIGNED_INT_5_9_9_9_REV&&(ve=s.RGB9_E5),J===s.UNSIGNED_INT_10F_11F_11F_REV&&(ve=s.R11F_G11F_B10F)),w===s.RGBA){const Je=Ae?$l:Nt.getTransfer(ge);J===s.FLOAT&&(ve=s.RGBA32F),J===s.HALF_FLOAT&&(ve=s.RGBA16F),J===s.UNSIGNED_BYTE&&(ve=Je===kt?s.SRGB8_ALPHA8:s.RGBA8),J===s.UNSIGNED_SHORT_4_4_4_4&&(ve=s.RGBA4),J===s.UNSIGNED_SHORT_5_5_5_1&&(ve=s.RGB5_A1)}return(ve===s.R16F||ve===s.R32F||ve===s.RG16F||ve===s.RG32F||ve===s.RGBA16F||ve===s.RGBA32F)&&e.get("EXT_color_buffer_float"),ve}function R(L,w){let J;return L?w===null||w===ss||w===Qo?J=s.DEPTH24_STENCIL8:w===Xi?J=s.DEPTH32F_STENCIL8:w===Jo&&(J=s.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):w===null||w===ss||w===Qo?J=s.DEPTH_COMPONENT24:w===Xi?J=s.DEPTH_COMPONENT32F:w===Jo&&(J=s.DEPTH_COMPONENT16),J}function z(L,w){return y(L)===!0||L.isFramebufferTexture&&L.minFilter!==vi&&L.minFilter!==Ei?Math.log2(Math.max(w.width,w.height))+1:L.mipmaps!==void 0&&L.mipmaps.length>0?L.mipmaps.length:L.isCompressedTexture&&Array.isArray(L.image)?w.mipmaps.length:1}function H(L){const w=L.target;w.removeEventListener("dispose",H),N(w),w.isVideoTexture&&v.delete(w)}function I(L){const w=L.target;w.removeEventListener("dispose",I),T(w)}function N(L){const w=r.get(L);if(w.__webglInit===void 0)return;const J=L.source,ge=_.get(J);if(ge){const Ae=ge[w.__cacheKey];Ae.usedTimes--,Ae.usedTimes===0&&C(L),Object.keys(ge).length===0&&_.delete(J)}r.remove(L)}function C(L){const w=r.get(L);s.deleteTexture(w.__webglTexture);const J=L.source,ge=_.get(J);delete ge[w.__cacheKey],u.memory.textures--}function T(L){const w=r.get(L);if(L.depthTexture&&(L.depthTexture.dispose(),r.remove(L.depthTexture)),L.isWebGLCubeRenderTarget)for(let ge=0;ge<6;ge++){if(Array.isArray(w.__webglFramebuffer[ge]))for(let Ae=0;Ae<w.__webglFramebuffer[ge].length;Ae++)s.deleteFramebuffer(w.__webglFramebuffer[ge][Ae]);else s.deleteFramebuffer(w.__webglFramebuffer[ge]);w.__webglDepthbuffer&&s.deleteRenderbuffer(w.__webglDepthbuffer[ge])}else{if(Array.isArray(w.__webglFramebuffer))for(let ge=0;ge<w.__webglFramebuffer.length;ge++)s.deleteFramebuffer(w.__webglFramebuffer[ge]);else s.deleteFramebuffer(w.__webglFramebuffer);if(w.__webglDepthbuffer&&s.deleteRenderbuffer(w.__webglDepthbuffer),w.__webglMultisampledFramebuffer&&s.deleteFramebuffer(w.__webglMultisampledFramebuffer),w.__webglColorRenderbuffer)for(let ge=0;ge<w.__webglColorRenderbuffer.length;ge++)w.__webglColorRenderbuffer[ge]&&s.deleteRenderbuffer(w.__webglColorRenderbuffer[ge]);w.__webglDepthRenderbuffer&&s.deleteRenderbuffer(w.__webglDepthRenderbuffer)}const J=L.textures;for(let ge=0,Ae=J.length;ge<Ae;ge++){const ve=r.get(J[ge]);ve.__webglTexture&&(s.deleteTexture(ve.__webglTexture),u.memory.textures--),r.remove(J[ge])}r.remove(L)}let F=0;function $(){F=0}function ee(){const L=F;return L>=o.maxTextures&&console.warn("THREE.WebGLTextures: Trying to use "+L+" texture units while this GPU supports only "+o.maxTextures),F+=1,L}function le(L){const w=[];return w.push(L.wrapS),w.push(L.wrapT),w.push(L.wrapR||0),w.push(L.magFilter),w.push(L.minFilter),w.push(L.anisotropy),w.push(L.internalFormat),w.push(L.format),w.push(L.type),w.push(L.generateMipmaps),w.push(L.premultiplyAlpha),w.push(L.flipY),w.push(L.unpackAlignment),w.push(L.colorSpace),w.join()}function ne(L,w){const J=r.get(L);if(L.isVideoTexture&&Re(L),L.isRenderTargetTexture===!1&&L.isExternalTexture!==!0&&L.version>0&&J.__version!==L.version){const ge=L.image;if(ge===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(ge.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{K(J,L,w);return}}else L.isExternalTexture&&(J.__webglTexture=L.sourceTexture?L.sourceTexture:null);t.bindTexture(s.TEXTURE_2D,J.__webglTexture,s.TEXTURE0+w)}function ce(L,w){const J=r.get(L);if(L.isRenderTargetTexture===!1&&L.version>0&&J.__version!==L.version){K(J,L,w);return}t.bindTexture(s.TEXTURE_2D_ARRAY,J.__webglTexture,s.TEXTURE0+w)}function re(L,w){const J=r.get(L);if(L.isRenderTargetTexture===!1&&L.version>0&&J.__version!==L.version){K(J,L,w);return}t.bindTexture(s.TEXTURE_3D,J.__webglTexture,s.TEXTURE0+w)}function V(L,w){const J=r.get(L);if(L.version>0&&J.__version!==L.version){oe(J,L,w);return}t.bindTexture(s.TEXTURE_CUBE_MAP,J.__webglTexture,s.TEXTURE0+w)}const me={[Nf]:s.REPEAT,[is]:s.CLAMP_TO_EDGE,[If]:s.MIRRORED_REPEAT},ie={[vi]:s.NEAREST,[Mx]:s.NEAREST_MIPMAP_NEAREST,[pl]:s.NEAREST_MIPMAP_LINEAR,[Ei]:s.LINEAR,[zu]:s.LINEAR_MIPMAP_NEAREST,[rs]:s.LINEAR_MIPMAP_LINEAR},P={[Ax]:s.NEVER,[Dx]:s.ALWAYS,[Rx]:s.LESS,[j0]:s.LEQUAL,[Cx]:s.EQUAL,[Lx]:s.GEQUAL,[bx]:s.GREATER,[Px]:s.NOTEQUAL};function B(L,w){if(w.type===Xi&&e.has("OES_texture_float_linear")===!1&&(w.magFilter===Ei||w.magFilter===zu||w.magFilter===pl||w.magFilter===rs||w.minFilter===Ei||w.minFilter===zu||w.minFilter===pl||w.minFilter===rs)&&console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),s.texParameteri(L,s.TEXTURE_WRAP_S,me[w.wrapS]),s.texParameteri(L,s.TEXTURE_WRAP_T,me[w.wrapT]),(L===s.TEXTURE_3D||L===s.TEXTURE_2D_ARRAY)&&s.texParameteri(L,s.TEXTURE_WRAP_R,me[w.wrapR]),s.texParameteri(L,s.TEXTURE_MAG_FILTER,ie[w.magFilter]),s.texParameteri(L,s.TEXTURE_MIN_FILTER,ie[w.minFilter]),w.compareFunction&&(s.texParameteri(L,s.TEXTURE_COMPARE_MODE,s.COMPARE_REF_TO_TEXTURE),s.texParameteri(L,s.TEXTURE_COMPARE_FUNC,P[w.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(w.magFilter===vi||w.minFilter!==pl&&w.minFilter!==rs||w.type===Xi&&e.has("OES_texture_float_linear")===!1)return;if(w.anisotropy>1||r.get(w).__currentAnisotropy){const J=e.get("EXT_texture_filter_anisotropic");s.texParameterf(L,J.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(w.anisotropy,o.getMaxAnisotropy())),r.get(w).__currentAnisotropy=w.anisotropy}}}function Z(L,w){let J=!1;L.__webglInit===void 0&&(L.__webglInit=!0,w.addEventListener("dispose",H));const ge=w.source;let Ae=_.get(ge);Ae===void 0&&(Ae={},_.set(ge,Ae));const ve=le(w);if(ve!==L.__cacheKey){Ae[ve]===void 0&&(Ae[ve]={texture:s.createTexture(),usedTimes:0},u.memory.textures++,J=!0),Ae[ve].usedTimes++;const Je=Ae[L.__cacheKey];Je!==void 0&&(Ae[L.__cacheKey].usedTimes--,Je.usedTimes===0&&C(w)),L.__cacheKey=ve,L.__webglTexture=Ae[ve].texture}return J}function ue(L,w,J){return Math.floor(Math.floor(L/J)/w)}function he(L,w,J,ge){const ve=L.updateRanges;if(ve.length===0)t.texSubImage2D(s.TEXTURE_2D,0,0,0,w.width,w.height,J,ge,w.data);else{ve.sort((Ie,He)=>Ie.start-He.start);let Je=0;for(let Ie=1;Ie<ve.length;Ie++){const He=ve[Je],ut=ve[Ie],Ze=He.start+He.count,Ve=ue(ut.start,w.width,4),ht=ue(He.start,w.width,4);ut.start<=Ze+1&&Ve===ht&&ue(ut.start+ut.count-1,w.width,4)===Ve?He.count=Math.max(He.count,ut.start+ut.count-He.start):(++Je,ve[Je]=ut)}ve.length=Je+1;const Le=s.getParameter(s.UNPACK_ROW_LENGTH),Ke=s.getParameter(s.UNPACK_SKIP_PIXELS),nt=s.getParameter(s.UNPACK_SKIP_ROWS);s.pixelStorei(s.UNPACK_ROW_LENGTH,w.width);for(let Ie=0,He=ve.length;Ie<He;Ie++){const ut=ve[Ie],Ze=Math.floor(ut.start/4),Ve=Math.ceil(ut.count/4),ht=Ze%w.width,X=Math.floor(Ze/w.width),Ue=Ve,ke=1;s.pixelStorei(s.UNPACK_SKIP_PIXELS,ht),s.pixelStorei(s.UNPACK_SKIP_ROWS,X),t.texSubImage2D(s.TEXTURE_2D,0,ht,X,Ue,ke,J,ge,w.data)}L.clearUpdateRanges(),s.pixelStorei(s.UNPACK_ROW_LENGTH,Le),s.pixelStorei(s.UNPACK_SKIP_PIXELS,Ke),s.pixelStorei(s.UNPACK_SKIP_ROWS,nt)}}function K(L,w,J){let ge=s.TEXTURE_2D;(w.isDataArrayTexture||w.isCompressedArrayTexture)&&(ge=s.TEXTURE_2D_ARRAY),w.isData3DTexture&&(ge=s.TEXTURE_3D);const Ae=Z(L,w),ve=w.source;t.bindTexture(ge,L.__webglTexture,s.TEXTURE0+J);const Je=r.get(ve);if(ve.version!==Je.__version||Ae===!0){t.activeTexture(s.TEXTURE0+J);const Le=Nt.getPrimaries(Nt.workingColorSpace),Ke=w.colorSpace===Tr?null:Nt.getPrimaries(w.colorSpace),nt=w.colorSpace===Tr||Le===Ke?s.NONE:s.BROWSER_DEFAULT_WEBGL;s.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,w.flipY),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),s.pixelStorei(s.UNPACK_ALIGNMENT,w.unpackAlignment),s.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,nt);let Ie=A(w.image,!1,o.maxTextureSize);Ie=ct(w,Ie);const He=l.convert(w.format,w.colorSpace),ut=l.convert(w.type);let Ze=D(w.internalFormat,He,ut,w.colorSpace,w.isVideoTexture);B(ge,w);let Ve;const ht=w.mipmaps,X=w.isVideoTexture!==!0,Ue=Je.__version===void 0||Ae===!0,ke=ve.dataReady,Xe=z(w,Ie);if(w.isDepthTexture)Ze=R(w.format===ta,w.type),Ue&&(X?t.texStorage2D(s.TEXTURE_2D,1,Ze,Ie.width,Ie.height):t.texImage2D(s.TEXTURE_2D,0,Ze,Ie.width,Ie.height,0,He,ut,null));else if(w.isDataTexture)if(ht.length>0){X&&Ue&&t.texStorage2D(s.TEXTURE_2D,Xe,Ze,ht[0].width,ht[0].height);for(let De=0,Te=ht.length;De<Te;De++)Ve=ht[De],X?ke&&t.texSubImage2D(s.TEXTURE_2D,De,0,0,Ve.width,Ve.height,He,ut,Ve.data):t.texImage2D(s.TEXTURE_2D,De,Ze,Ve.width,Ve.height,0,He,ut,Ve.data);w.generateMipmaps=!1}else X?(Ue&&t.texStorage2D(s.TEXTURE_2D,Xe,Ze,Ie.width,Ie.height),ke&&he(w,Ie,He,ut)):t.texImage2D(s.TEXTURE_2D,0,Ze,Ie.width,Ie.height,0,He,ut,Ie.data);else if(w.isCompressedTexture)if(w.isCompressedArrayTexture){X&&Ue&&t.texStorage3D(s.TEXTURE_2D_ARRAY,Xe,Ze,ht[0].width,ht[0].height,Ie.depth);for(let De=0,Te=ht.length;De<Te;De++)if(Ve=ht[De],w.format!==gi)if(He!==null)if(X){if(ke)if(w.layerUpdates.size>0){const et=Zm(Ve.width,Ve.height,w.format,w.type);for(const xt of w.layerUpdates){const Ne=Ve.data.subarray(xt*et/Ve.data.BYTES_PER_ELEMENT,(xt+1)*et/Ve.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,De,0,0,xt,Ve.width,Ve.height,1,He,Ne)}w.clearLayerUpdates()}else t.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,De,0,0,0,Ve.width,Ve.height,Ie.depth,He,Ve.data)}else t.compressedTexImage3D(s.TEXTURE_2D_ARRAY,De,Ze,Ve.width,Ve.height,Ie.depth,0,Ve.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else X?ke&&t.texSubImage3D(s.TEXTURE_2D_ARRAY,De,0,0,0,Ve.width,Ve.height,Ie.depth,He,ut,Ve.data):t.texImage3D(s.TEXTURE_2D_ARRAY,De,Ze,Ve.width,Ve.height,Ie.depth,0,He,ut,Ve.data)}else{X&&Ue&&t.texStorage2D(s.TEXTURE_2D,Xe,Ze,ht[0].width,ht[0].height);for(let De=0,Te=ht.length;De<Te;De++)Ve=ht[De],w.format!==gi?He!==null?X?ke&&t.compressedTexSubImage2D(s.TEXTURE_2D,De,0,0,Ve.width,Ve.height,He,Ve.data):t.compressedTexImage2D(s.TEXTURE_2D,De,Ze,Ve.width,Ve.height,0,Ve.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):X?ke&&t.texSubImage2D(s.TEXTURE_2D,De,0,0,Ve.width,Ve.height,He,ut,Ve.data):t.texImage2D(s.TEXTURE_2D,De,Ze,Ve.width,Ve.height,0,He,ut,Ve.data)}else if(w.isDataArrayTexture)if(X){if(Ue&&t.texStorage3D(s.TEXTURE_2D_ARRAY,Xe,Ze,Ie.width,Ie.height,Ie.depth),ke)if(w.layerUpdates.size>0){const De=Zm(Ie.width,Ie.height,w.format,w.type);for(const Te of w.layerUpdates){const et=Ie.data.subarray(Te*De/Ie.data.BYTES_PER_ELEMENT,(Te+1)*De/Ie.data.BYTES_PER_ELEMENT);t.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,Te,Ie.width,Ie.height,1,He,ut,et)}w.clearLayerUpdates()}else t.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,0,Ie.width,Ie.height,Ie.depth,He,ut,Ie.data)}else t.texImage3D(s.TEXTURE_2D_ARRAY,0,Ze,Ie.width,Ie.height,Ie.depth,0,He,ut,Ie.data);else if(w.isData3DTexture)X?(Ue&&t.texStorage3D(s.TEXTURE_3D,Xe,Ze,Ie.width,Ie.height,Ie.depth),ke&&t.texSubImage3D(s.TEXTURE_3D,0,0,0,0,Ie.width,Ie.height,Ie.depth,He,ut,Ie.data)):t.texImage3D(s.TEXTURE_3D,0,Ze,Ie.width,Ie.height,Ie.depth,0,He,ut,Ie.data);else if(w.isFramebufferTexture){if(Ue)if(X)t.texStorage2D(s.TEXTURE_2D,Xe,Ze,Ie.width,Ie.height);else{let De=Ie.width,Te=Ie.height;for(let et=0;et<Xe;et++)t.texImage2D(s.TEXTURE_2D,et,Ze,De,Te,0,He,ut,null),De>>=1,Te>>=1}}else if(ht.length>0){if(X&&Ue){const De=ft(ht[0]);t.texStorage2D(s.TEXTURE_2D,Xe,Ze,De.width,De.height)}for(let De=0,Te=ht.length;De<Te;De++)Ve=ht[De],X?ke&&t.texSubImage2D(s.TEXTURE_2D,De,0,0,He,ut,Ve):t.texImage2D(s.TEXTURE_2D,De,Ze,He,ut,Ve);w.generateMipmaps=!1}else if(X){if(Ue){const De=ft(Ie);t.texStorage2D(s.TEXTURE_2D,Xe,Ze,De.width,De.height)}ke&&t.texSubImage2D(s.TEXTURE_2D,0,0,0,He,ut,Ie)}else t.texImage2D(s.TEXTURE_2D,0,Ze,He,ut,Ie);y(w)&&x(ge),Je.__version=ve.version,w.onUpdate&&w.onUpdate(w)}L.__version=w.version}function oe(L,w,J){if(w.image.length!==6)return;const ge=Z(L,w),Ae=w.source;t.bindTexture(s.TEXTURE_CUBE_MAP,L.__webglTexture,s.TEXTURE0+J);const ve=r.get(Ae);if(Ae.version!==ve.__version||ge===!0){t.activeTexture(s.TEXTURE0+J);const Je=Nt.getPrimaries(Nt.workingColorSpace),Le=w.colorSpace===Tr?null:Nt.getPrimaries(w.colorSpace),Ke=w.colorSpace===Tr||Je===Le?s.NONE:s.BROWSER_DEFAULT_WEBGL;s.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,w.flipY),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),s.pixelStorei(s.UNPACK_ALIGNMENT,w.unpackAlignment),s.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,Ke);const nt=w.isCompressedTexture||w.image[0].isCompressedTexture,Ie=w.image[0]&&w.image[0].isDataTexture,He=[];for(let Te=0;Te<6;Te++)!nt&&!Ie?He[Te]=A(w.image[Te],!0,o.maxCubemapSize):He[Te]=Ie?w.image[Te].image:w.image[Te],He[Te]=ct(w,He[Te]);const ut=He[0],Ze=l.convert(w.format,w.colorSpace),Ve=l.convert(w.type),ht=D(w.internalFormat,Ze,Ve,w.colorSpace),X=w.isVideoTexture!==!0,Ue=ve.__version===void 0||ge===!0,ke=Ae.dataReady;let Xe=z(w,ut);B(s.TEXTURE_CUBE_MAP,w);let De;if(nt){X&&Ue&&t.texStorage2D(s.TEXTURE_CUBE_MAP,Xe,ht,ut.width,ut.height);for(let Te=0;Te<6;Te++){De=He[Te].mipmaps;for(let et=0;et<De.length;et++){const xt=De[et];w.format!==gi?Ze!==null?X?ke&&t.compressedTexSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et,0,0,xt.width,xt.height,Ze,xt.data):t.compressedTexImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et,ht,xt.width,xt.height,0,xt.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):X?ke&&t.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et,0,0,xt.width,xt.height,Ze,Ve,xt.data):t.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et,ht,xt.width,xt.height,0,Ze,Ve,xt.data)}}}else{if(De=w.mipmaps,X&&Ue){De.length>0&&Xe++;const Te=ft(He[0]);t.texStorage2D(s.TEXTURE_CUBE_MAP,Xe,ht,Te.width,Te.height)}for(let Te=0;Te<6;Te++)if(Ie){X?ke&&t.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,0,0,0,He[Te].width,He[Te].height,Ze,Ve,He[Te].data):t.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,0,ht,He[Te].width,He[Te].height,0,Ze,Ve,He[Te].data);for(let et=0;et<De.length;et++){const Ne=De[et].image[Te].image;X?ke&&t.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et+1,0,0,Ne.width,Ne.height,Ze,Ve,Ne.data):t.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et+1,ht,Ne.width,Ne.height,0,Ze,Ve,Ne.data)}}else{X?ke&&t.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,0,0,0,Ze,Ve,He[Te]):t.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,0,ht,Ze,Ve,He[Te]);for(let et=0;et<De.length;et++){const xt=De[et];X?ke&&t.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et+1,0,0,Ze,Ve,xt.image[Te]):t.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Te,et+1,ht,Ze,Ve,xt.image[Te])}}}y(w)&&x(s.TEXTURE_CUBE_MAP),ve.__version=Ae.version,w.onUpdate&&w.onUpdate(w)}L.__version=w.version}function Ee(L,w,J,ge,Ae,ve){const Je=l.convert(J.format,J.colorSpace),Le=l.convert(J.type),Ke=D(J.internalFormat,Je,Le,J.colorSpace),nt=r.get(w),Ie=r.get(J);if(Ie.__renderTarget=w,!nt.__hasExternalTextures){const He=Math.max(1,w.width>>ve),ut=Math.max(1,w.height>>ve);Ae===s.TEXTURE_3D||Ae===s.TEXTURE_2D_ARRAY?t.texImage3D(Ae,ve,Ke,He,ut,w.depth,0,Je,Le,null):t.texImage2D(Ae,ve,Ke,He,ut,0,Je,Le,null)}t.bindFramebuffer(s.FRAMEBUFFER,L),xe(w)?f.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,ge,Ae,Ie.__webglTexture,0,be(w)):(Ae===s.TEXTURE_2D||Ae>=s.TEXTURE_CUBE_MAP_POSITIVE_X&&Ae<=s.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&s.framebufferTexture2D(s.FRAMEBUFFER,ge,Ae,Ie.__webglTexture,ve),t.bindFramebuffer(s.FRAMEBUFFER,null)}function ye(L,w,J){if(s.bindRenderbuffer(s.RENDERBUFFER,L),w.depthBuffer){const ge=w.depthTexture,Ae=ge&&ge.isDepthTexture?ge.type:null,ve=R(w.stencilBuffer,Ae),Je=w.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,Le=be(w);xe(w)?f.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,Le,ve,w.width,w.height):J?s.renderbufferStorageMultisample(s.RENDERBUFFER,Le,ve,w.width,w.height):s.renderbufferStorage(s.RENDERBUFFER,ve,w.width,w.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,Je,s.RENDERBUFFER,L)}else{const ge=w.textures;for(let Ae=0;Ae<ge.length;Ae++){const ve=ge[Ae],Je=l.convert(ve.format,ve.colorSpace),Le=l.convert(ve.type),Ke=D(ve.internalFormat,Je,Le,ve.colorSpace),nt=be(w);J&&xe(w)===!1?s.renderbufferStorageMultisample(s.RENDERBUFFER,nt,Ke,w.width,w.height):xe(w)?f.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,nt,Ke,w.width,w.height):s.renderbufferStorage(s.RENDERBUFFER,Ke,w.width,w.height)}}s.bindRenderbuffer(s.RENDERBUFFER,null)}function we(L,w){if(w&&w.isWebGLCubeRenderTarget)throw new Error("Depth Texture with cube render targets is not supported");if(t.bindFramebuffer(s.FRAMEBUFFER,L),!(w.depthTexture&&w.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const ge=r.get(w.depthTexture);ge.__renderTarget=w,(!ge.__webglTexture||w.depthTexture.image.width!==w.width||w.depthTexture.image.height!==w.height)&&(w.depthTexture.image.width=w.width,w.depthTexture.image.height=w.height,w.depthTexture.needsUpdate=!0),ne(w.depthTexture,0);const Ae=ge.__webglTexture,ve=be(w);if(w.depthTexture.format===ea)xe(w)?f.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,s.DEPTH_ATTACHMENT,s.TEXTURE_2D,Ae,0,ve):s.framebufferTexture2D(s.FRAMEBUFFER,s.DEPTH_ATTACHMENT,s.TEXTURE_2D,Ae,0);else if(w.depthTexture.format===ta)xe(w)?f.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,s.DEPTH_STENCIL_ATTACHMENT,s.TEXTURE_2D,Ae,0,ve):s.framebufferTexture2D(s.FRAMEBUFFER,s.DEPTH_STENCIL_ATTACHMENT,s.TEXTURE_2D,Ae,0);else throw new Error("Unknown depthTexture format")}function tt(L){const w=r.get(L),J=L.isWebGLCubeRenderTarget===!0;if(w.__boundDepthTexture!==L.depthTexture){const ge=L.depthTexture;if(w.__depthDisposeCallback&&w.__depthDisposeCallback(),ge){const Ae=()=>{delete w.__boundDepthTexture,delete w.__depthDisposeCallback,ge.removeEventListener("dispose",Ae)};ge.addEventListener("dispose",Ae),w.__depthDisposeCallback=Ae}w.__boundDepthTexture=ge}if(L.depthTexture&&!w.__autoAllocateDepthBuffer){if(J)throw new Error("target.depthTexture not supported in Cube render targets");const ge=L.texture.mipmaps;ge&&ge.length>0?we(w.__webglFramebuffer[0],L):we(w.__webglFramebuffer,L)}else if(J){w.__webglDepthbuffer=[];for(let ge=0;ge<6;ge++)if(t.bindFramebuffer(s.FRAMEBUFFER,w.__webglFramebuffer[ge]),w.__webglDepthbuffer[ge]===void 0)w.__webglDepthbuffer[ge]=s.createRenderbuffer(),ye(w.__webglDepthbuffer[ge],L,!1);else{const Ae=L.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ve=w.__webglDepthbuffer[ge];s.bindRenderbuffer(s.RENDERBUFFER,ve),s.framebufferRenderbuffer(s.FRAMEBUFFER,Ae,s.RENDERBUFFER,ve)}}else{const ge=L.texture.mipmaps;if(ge&&ge.length>0?t.bindFramebuffer(s.FRAMEBUFFER,w.__webglFramebuffer[0]):t.bindFramebuffer(s.FRAMEBUFFER,w.__webglFramebuffer),w.__webglDepthbuffer===void 0)w.__webglDepthbuffer=s.createRenderbuffer(),ye(w.__webglDepthbuffer,L,!1);else{const Ae=L.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ve=w.__webglDepthbuffer;s.bindRenderbuffer(s.RENDERBUFFER,ve),s.framebufferRenderbuffer(s.FRAMEBUFFER,Ae,s.RENDERBUFFER,ve)}}t.bindFramebuffer(s.FRAMEBUFFER,null)}function at(L,w,J){const ge=r.get(L);w!==void 0&&Ee(ge.__webglFramebuffer,L,L.texture,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,0),J!==void 0&&tt(L)}function U(L){const w=L.texture,J=r.get(L),ge=r.get(w);L.addEventListener("dispose",I);const Ae=L.textures,ve=L.isWebGLCubeRenderTarget===!0,Je=Ae.length>1;if(Je||(ge.__webglTexture===void 0&&(ge.__webglTexture=s.createTexture()),ge.__version=w.version,u.memory.textures++),ve){J.__webglFramebuffer=[];for(let Le=0;Le<6;Le++)if(w.mipmaps&&w.mipmaps.length>0){J.__webglFramebuffer[Le]=[];for(let Ke=0;Ke<w.mipmaps.length;Ke++)J.__webglFramebuffer[Le][Ke]=s.createFramebuffer()}else J.__webglFramebuffer[Le]=s.createFramebuffer()}else{if(w.mipmaps&&w.mipmaps.length>0){J.__webglFramebuffer=[];for(let Le=0;Le<w.mipmaps.length;Le++)J.__webglFramebuffer[Le]=s.createFramebuffer()}else J.__webglFramebuffer=s.createFramebuffer();if(Je)for(let Le=0,Ke=Ae.length;Le<Ke;Le++){const nt=r.get(Ae[Le]);nt.__webglTexture===void 0&&(nt.__webglTexture=s.createTexture(),u.memory.textures++)}if(L.samples>0&&xe(L)===!1){J.__webglMultisampledFramebuffer=s.createFramebuffer(),J.__webglColorRenderbuffer=[],t.bindFramebuffer(s.FRAMEBUFFER,J.__webglMultisampledFramebuffer);for(let Le=0;Le<Ae.length;Le++){const Ke=Ae[Le];J.__webglColorRenderbuffer[Le]=s.createRenderbuffer(),s.bindRenderbuffer(s.RENDERBUFFER,J.__webglColorRenderbuffer[Le]);const nt=l.convert(Ke.format,Ke.colorSpace),Ie=l.convert(Ke.type),He=D(Ke.internalFormat,nt,Ie,Ke.colorSpace,L.isXRRenderTarget===!0),ut=be(L);s.renderbufferStorageMultisample(s.RENDERBUFFER,ut,He,L.width,L.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+Le,s.RENDERBUFFER,J.__webglColorRenderbuffer[Le])}s.bindRenderbuffer(s.RENDERBUFFER,null),L.depthBuffer&&(J.__webglDepthRenderbuffer=s.createRenderbuffer(),ye(J.__webglDepthRenderbuffer,L,!0)),t.bindFramebuffer(s.FRAMEBUFFER,null)}}if(ve){t.bindTexture(s.TEXTURE_CUBE_MAP,ge.__webglTexture),B(s.TEXTURE_CUBE_MAP,w);for(let Le=0;Le<6;Le++)if(w.mipmaps&&w.mipmaps.length>0)for(let Ke=0;Ke<w.mipmaps.length;Ke++)Ee(J.__webglFramebuffer[Le][Ke],L,w,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+Le,Ke);else Ee(J.__webglFramebuffer[Le],L,w,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+Le,0);y(w)&&x(s.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Je){for(let Le=0,Ke=Ae.length;Le<Ke;Le++){const nt=Ae[Le],Ie=r.get(nt);let He=s.TEXTURE_2D;(L.isWebGL3DRenderTarget||L.isWebGLArrayRenderTarget)&&(He=L.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),t.bindTexture(He,Ie.__webglTexture),B(He,nt),Ee(J.__webglFramebuffer,L,nt,s.COLOR_ATTACHMENT0+Le,He,0),y(nt)&&x(He)}t.unbindTexture()}else{let Le=s.TEXTURE_2D;if((L.isWebGL3DRenderTarget||L.isWebGLArrayRenderTarget)&&(Le=L.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),t.bindTexture(Le,ge.__webglTexture),B(Le,w),w.mipmaps&&w.mipmaps.length>0)for(let Ke=0;Ke<w.mipmaps.length;Ke++)Ee(J.__webglFramebuffer[Ke],L,w,s.COLOR_ATTACHMENT0,Le,Ke);else Ee(J.__webglFramebuffer,L,w,s.COLOR_ATTACHMENT0,Le,0);y(w)&&x(Le),t.unbindTexture()}L.depthBuffer&&tt(L)}function Me(L){const w=L.textures;for(let J=0,ge=w.length;J<ge;J++){const Ae=w[J];if(y(Ae)){const ve=O(L),Je=r.get(Ae).__webglTexture;t.bindTexture(ve,Je),x(ve),t.unbindTexture()}}}const _e=[],Se=[];function fe(L){if(L.samples>0){if(xe(L)===!1){const w=L.textures,J=L.width,ge=L.height;let Ae=s.COLOR_BUFFER_BIT;const ve=L.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,Je=r.get(L),Le=w.length>1;if(Le)for(let nt=0;nt<w.length;nt++)t.bindFramebuffer(s.FRAMEBUFFER,Je.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+nt,s.RENDERBUFFER,null),t.bindFramebuffer(s.FRAMEBUFFER,Je.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+nt,s.TEXTURE_2D,null,0);t.bindFramebuffer(s.READ_FRAMEBUFFER,Je.__webglMultisampledFramebuffer);const Ke=L.texture.mipmaps;Ke&&Ke.length>0?t.bindFramebuffer(s.DRAW_FRAMEBUFFER,Je.__webglFramebuffer[0]):t.bindFramebuffer(s.DRAW_FRAMEBUFFER,Je.__webglFramebuffer);for(let nt=0;nt<w.length;nt++){if(L.resolveDepthBuffer&&(L.depthBuffer&&(Ae|=s.DEPTH_BUFFER_BIT),L.stencilBuffer&&L.resolveStencilBuffer&&(Ae|=s.STENCIL_BUFFER_BIT)),Le){s.framebufferRenderbuffer(s.READ_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.RENDERBUFFER,Je.__webglColorRenderbuffer[nt]);const Ie=r.get(w[nt]).__webglTexture;s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,Ie,0)}s.blitFramebuffer(0,0,J,ge,0,0,J,ge,Ae,s.NEAREST),d===!0&&(_e.length=0,Se.length=0,_e.push(s.COLOR_ATTACHMENT0+nt),L.depthBuffer&&L.resolveDepthBuffer===!1&&(_e.push(ve),Se.push(ve),s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,Se)),s.invalidateFramebuffer(s.READ_FRAMEBUFFER,_e))}if(t.bindFramebuffer(s.READ_FRAMEBUFFER,null),t.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),Le)for(let nt=0;nt<w.length;nt++){t.bindFramebuffer(s.FRAMEBUFFER,Je.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+nt,s.RENDERBUFFER,Je.__webglColorRenderbuffer[nt]);const Ie=r.get(w[nt]).__webglTexture;t.bindFramebuffer(s.FRAMEBUFFER,Je.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+nt,s.TEXTURE_2D,Ie,0)}t.bindFramebuffer(s.DRAW_FRAMEBUFFER,Je.__webglMultisampledFramebuffer)}else if(L.depthBuffer&&L.resolveDepthBuffer===!1&&d){const w=L.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,[w])}}}function be(L){return Math.min(o.maxSamples,L.samples)}function xe(L){const w=r.get(L);return L.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&w.__useRenderToTexture!==!1}function Re(L){const w=u.render.frame;v.get(L)!==w&&(v.set(L,w),L.update())}function ct(L,w){const J=L.colorSpace,ge=L.format,Ae=L.type;return L.isCompressedTexture===!0||L.isVideoTexture===!0||J!==to&&J!==Tr&&(Nt.getTransfer(J)===kt?(ge!==gi||Ae!==Ai)&&console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):console.error("THREE.WebGLTextures: Unsupported texture color space:",J)),w}function ft(L){return typeof HTMLImageElement<"u"&&L instanceof HTMLImageElement?(p.width=L.naturalWidth||L.width,p.height=L.naturalHeight||L.height):typeof VideoFrame<"u"&&L instanceof VideoFrame?(p.width=L.displayWidth,p.height=L.displayHeight):(p.width=L.width,p.height=L.height),p}this.allocateTextureUnit=ee,this.resetTextureUnits=$,this.setTexture2D=ne,this.setTexture2DArray=ce,this.setTexture3D=re,this.setTextureCube=V,this.rebindTextures=at,this.setupRenderTarget=U,this.updateRenderTargetMipmap=Me,this.updateMultisampleRenderTarget=fe,this.setupDepthRenderbuffer=tt,this.setupFrameBufferTexture=Ee,this.useMultisampledRTT=xe}function Aw(s,e){function t(r,o=Tr){let l;const u=Nt.getTransfer(o);if(r===Ai)return s.UNSIGNED_BYTE;if(r===yd)return s.UNSIGNED_SHORT_4_4_4_4;if(r===Sd)return s.UNSIGNED_SHORT_5_5_5_1;if(r===B0)return s.UNSIGNED_INT_5_9_9_9_REV;if(r===z0)return s.UNSIGNED_INT_10F_11F_11F_REV;if(r===O0)return s.BYTE;if(r===k0)return s.SHORT;if(r===Jo)return s.UNSIGNED_SHORT;if(r===xd)return s.INT;if(r===ss)return s.UNSIGNED_INT;if(r===Xi)return s.FLOAT;if(r===oa)return s.HALF_FLOAT;if(r===H0)return s.ALPHA;if(r===V0)return s.RGB;if(r===gi)return s.RGBA;if(r===ea)return s.DEPTH_COMPONENT;if(r===ta)return s.DEPTH_STENCIL;if(r===G0)return s.RED;if(r===Md)return s.RED_INTEGER;if(r===W0)return s.RG;if(r===Ed)return s.RG_INTEGER;if(r===wd)return s.RGBA_INTEGER;if(r===Gl||r===Wl||r===Xl||r===jl)if(u===kt)if(l=e.get("WEBGL_compressed_texture_s3tc_srgb"),l!==null){if(r===Gl)return l.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(r===Wl)return l.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(r===Xl)return l.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(r===jl)return l.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(l=e.get("WEBGL_compressed_texture_s3tc"),l!==null){if(r===Gl)return l.COMPRESSED_RGB_S3TC_DXT1_EXT;if(r===Wl)return l.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(r===Xl)return l.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(r===jl)return l.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(r===Uf||r===Ff||r===Of||r===kf)if(l=e.get("WEBGL_compressed_texture_pvrtc"),l!==null){if(r===Uf)return l.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(r===Ff)return l.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(r===Of)return l.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(r===kf)return l.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(r===Bf||r===zf||r===Hf)if(l=e.get("WEBGL_compressed_texture_etc"),l!==null){if(r===Bf||r===zf)return u===kt?l.COMPRESSED_SRGB8_ETC2:l.COMPRESSED_RGB8_ETC2;if(r===Hf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:l.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(r===Vf||r===Gf||r===Wf||r===Xf||r===jf||r===qf||r===Yf||r===$f||r===Kf||r===Zf||r===Jf||r===Qf||r===ed||r===td)if(l=e.get("WEBGL_compressed_texture_astc"),l!==null){if(r===Vf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:l.COMPRESSED_RGBA_ASTC_4x4_KHR;if(r===Gf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:l.COMPRESSED_RGBA_ASTC_5x4_KHR;if(r===Wf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:l.COMPRESSED_RGBA_ASTC_5x5_KHR;if(r===Xf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:l.COMPRESSED_RGBA_ASTC_6x5_KHR;if(r===jf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:l.COMPRESSED_RGBA_ASTC_6x6_KHR;if(r===qf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:l.COMPRESSED_RGBA_ASTC_8x5_KHR;if(r===Yf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:l.COMPRESSED_RGBA_ASTC_8x6_KHR;if(r===$f)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:l.COMPRESSED_RGBA_ASTC_8x8_KHR;if(r===Kf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:l.COMPRESSED_RGBA_ASTC_10x5_KHR;if(r===Zf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:l.COMPRESSED_RGBA_ASTC_10x6_KHR;if(r===Jf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:l.COMPRESSED_RGBA_ASTC_10x8_KHR;if(r===Qf)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:l.COMPRESSED_RGBA_ASTC_10x10_KHR;if(r===ed)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:l.COMPRESSED_RGBA_ASTC_12x10_KHR;if(r===td)return u===kt?l.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:l.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(r===nd||r===id||r===rd)if(l=e.get("EXT_texture_compression_bptc"),l!==null){if(r===nd)return u===kt?l.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:l.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(r===id)return l.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(r===rd)return l.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(r===sd||r===od||r===ad||r===ld)if(l=e.get("EXT_texture_compression_rgtc"),l!==null){if(r===sd)return l.COMPRESSED_RED_RGTC1_EXT;if(r===od)return l.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(r===ad)return l.COMPRESSED_RED_GREEN_RGTC2_EXT;if(r===ld)return l.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return r===Qo?s.UNSIGNED_INT_24_8:s[r]!==void 0?s[r]:null}return{convert:t}}const Rw=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Cw=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class bw{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const r=new ig(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=r}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,r=new br({vertexShader:Rw,fragmentShader:Cw,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new an(new ua(20,20),r)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class Pw extends so{constructor(e,t){super();const r=this;let o=null,l=1,u=null,f="local-floor",d=1,p=null,v=null,g=null,_=null,S=null,M=null;const A=typeof XRWebGLBinding<"u",y=new bw,x={},O=t.getContextAttributes();let D=null,R=null;const z=[],H=[],I=new Ge;let N=null;const C=new ri;C.viewport=new Zt;const T=new ri;T.viewport=new Zt;const F=[C,T],$=new Ky;let ee=null,le=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(K){let oe=z[K];return oe===void 0&&(oe=new uf,z[K]=oe),oe.getTargetRaySpace()},this.getControllerGrip=function(K){let oe=z[K];return oe===void 0&&(oe=new uf,z[K]=oe),oe.getGripSpace()},this.getHand=function(K){let oe=z[K];return oe===void 0&&(oe=new uf,z[K]=oe),oe.getHandSpace()};function ne(K){const oe=H.indexOf(K.inputSource);if(oe===-1)return;const Ee=z[oe];Ee!==void 0&&(Ee.update(K.inputSource,K.frame,p||u),Ee.dispatchEvent({type:K.type,data:K.inputSource}))}function ce(){o.removeEventListener("select",ne),o.removeEventListener("selectstart",ne),o.removeEventListener("selectend",ne),o.removeEventListener("squeeze",ne),o.removeEventListener("squeezestart",ne),o.removeEventListener("squeezeend",ne),o.removeEventListener("end",ce),o.removeEventListener("inputsourceschange",re);for(let K=0;K<z.length;K++){const oe=H[K];oe!==null&&(H[K]=null,z[K].disconnect(oe))}ee=null,le=null,y.reset();for(const K in x)delete x[K];e.setRenderTarget(D),S=null,_=null,g=null,o=null,R=null,he.stop(),r.isPresenting=!1,e.setPixelRatio(N),e.setSize(I.width,I.height,!1),r.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(K){l=K,r.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(K){f=K,r.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return p||u},this.setReferenceSpace=function(K){p=K},this.getBaseLayer=function(){return _!==null?_:S},this.getBinding=function(){return g===null&&A&&(g=new XRWebGLBinding(o,t)),g},this.getFrame=function(){return M},this.getSession=function(){return o},this.setSession=async function(K){if(o=K,o!==null){if(D=e.getRenderTarget(),o.addEventListener("select",ne),o.addEventListener("selectstart",ne),o.addEventListener("selectend",ne),o.addEventListener("squeeze",ne),o.addEventListener("squeezestart",ne),o.addEventListener("squeezeend",ne),o.addEventListener("end",ce),o.addEventListener("inputsourceschange",re),O.xrCompatible!==!0&&await t.makeXRCompatible(),N=e.getPixelRatio(),e.getSize(I),A&&"createProjectionLayer"in XRWebGLBinding.prototype){let Ee=null,ye=null,we=null;O.depth&&(we=O.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Ee=O.stencil?ta:ea,ye=O.stencil?Qo:ss);const tt={colorFormat:t.RGBA8,depthFormat:we,scaleFactor:l};g=this.getBinding(),_=g.createProjectionLayer(tt),o.updateRenderState({layers:[_]}),e.setPixelRatio(1),e.setSize(_.textureWidth,_.textureHeight,!1),R=new os(_.textureWidth,_.textureHeight,{format:gi,type:Ai,depthTexture:new ng(_.textureWidth,_.textureHeight,ye,void 0,void 0,void 0,void 0,void 0,void 0,Ee),stencilBuffer:O.stencil,colorSpace:e.outputColorSpace,samples:O.antialias?4:0,resolveDepthBuffer:_.ignoreDepthValues===!1,resolveStencilBuffer:_.ignoreDepthValues===!1})}else{const Ee={antialias:O.antialias,alpha:!0,depth:O.depth,stencil:O.stencil,framebufferScaleFactor:l};S=new XRWebGLLayer(o,t,Ee),o.updateRenderState({baseLayer:S}),e.setPixelRatio(1),e.setSize(S.framebufferWidth,S.framebufferHeight,!1),R=new os(S.framebufferWidth,S.framebufferHeight,{format:gi,type:Ai,colorSpace:e.outputColorSpace,stencilBuffer:O.stencil,resolveDepthBuffer:S.ignoreDepthValues===!1,resolveStencilBuffer:S.ignoreDepthValues===!1})}R.isXRRenderTarget=!0,this.setFoveation(d),p=null,u=await o.requestReferenceSpace(f),he.setContext(o),he.start(),r.isPresenting=!0,r.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(o!==null)return o.environmentBlendMode},this.getDepthTexture=function(){return y.getDepthTexture()};function re(K){for(let oe=0;oe<K.removed.length;oe++){const Ee=K.removed[oe],ye=H.indexOf(Ee);ye>=0&&(H[ye]=null,z[ye].disconnect(Ee))}for(let oe=0;oe<K.added.length;oe++){const Ee=K.added[oe];let ye=H.indexOf(Ee);if(ye===-1){for(let tt=0;tt<z.length;tt++)if(tt>=H.length){H.push(Ee),ye=tt;break}else if(H[tt]===null){H[tt]=Ee,ye=tt;break}if(ye===-1)break}const we=z[ye];we&&we.connect(Ee)}}const V=new Q,me=new Q;function ie(K,oe,Ee){V.setFromMatrixPosition(oe.matrixWorld),me.setFromMatrixPosition(Ee.matrixWorld);const ye=V.distanceTo(me),we=oe.projectionMatrix.elements,tt=Ee.projectionMatrix.elements,at=we[14]/(we[10]-1),U=we[14]/(we[10]+1),Me=(we[9]+1)/we[5],_e=(we[9]-1)/we[5],Se=(we[8]-1)/we[0],fe=(tt[8]+1)/tt[0],be=at*Se,xe=at*fe,Re=ye/(-Se+fe),ct=Re*-Se;if(oe.matrixWorld.decompose(K.position,K.quaternion,K.scale),K.translateX(ct),K.translateZ(Re),K.matrixWorld.compose(K.position,K.quaternion,K.scale),K.matrixWorldInverse.copy(K.matrixWorld).invert(),we[10]===-1)K.projectionMatrix.copy(oe.projectionMatrix),K.projectionMatrixInverse.copy(oe.projectionMatrixInverse);else{const ft=at+Re,L=U+Re,w=be-ct,J=xe+(ye-ct),ge=Me*U/L*ft,Ae=_e*U/L*ft;K.projectionMatrix.makePerspective(w,J,ge,Ae,ft,L),K.projectionMatrixInverse.copy(K.projectionMatrix).invert()}}function P(K,oe){oe===null?K.matrixWorld.copy(K.matrix):K.matrixWorld.multiplyMatrices(oe.matrixWorld,K.matrix),K.matrixWorldInverse.copy(K.matrixWorld).invert()}this.updateCamera=function(K){if(o===null)return;let oe=K.near,Ee=K.far;y.texture!==null&&(y.depthNear>0&&(oe=y.depthNear),y.depthFar>0&&(Ee=y.depthFar)),$.near=T.near=C.near=oe,$.far=T.far=C.far=Ee,(ee!==$.near||le!==$.far)&&(o.updateRenderState({depthNear:$.near,depthFar:$.far}),ee=$.near,le=$.far),$.layers.mask=K.layers.mask|6,C.layers.mask=$.layers.mask&3,T.layers.mask=$.layers.mask&5;const ye=K.parent,we=$.cameras;P($,ye);for(let tt=0;tt<we.length;tt++)P(we[tt],ye);we.length===2?ie($,C,T):$.projectionMatrix.copy(C.projectionMatrix),B(K,$,ye)};function B(K,oe,Ee){Ee===null?K.matrix.copy(oe.matrixWorld):(K.matrix.copy(Ee.matrixWorld),K.matrix.invert(),K.matrix.multiply(oe.matrixWorld)),K.matrix.decompose(K.position,K.quaternion,K.scale),K.updateMatrixWorld(!0),K.projectionMatrix.copy(oe.projectionMatrix),K.projectionMatrixInverse.copy(oe.projectionMatrixInverse),K.isPerspectiveCamera&&(K.fov=cd*2*Math.atan(1/K.projectionMatrix.elements[5]),K.zoom=1)}this.getCamera=function(){return $},this.getFoveation=function(){if(!(_===null&&S===null))return d},this.setFoveation=function(K){d=K,_!==null&&(_.fixedFoveation=K),S!==null&&S.fixedFoveation!==void 0&&(S.fixedFoveation=K)},this.hasDepthSensing=function(){return y.texture!==null},this.getDepthSensingMesh=function(){return y.getMesh($)},this.getCameraTexture=function(K){return x[K]};let Z=null;function ue(K,oe){if(v=oe.getViewerPose(p||u),M=oe,v!==null){const Ee=v.views;S!==null&&(e.setRenderTargetFramebuffer(R,S.framebuffer),e.setRenderTarget(R));let ye=!1;Ee.length!==$.cameras.length&&($.cameras.length=0,ye=!0);for(let U=0;U<Ee.length;U++){const Me=Ee[U];let _e=null;if(S!==null)_e=S.getViewport(Me);else{const fe=g.getViewSubImage(_,Me);_e=fe.viewport,U===0&&(e.setRenderTargetTextures(R,fe.colorTexture,fe.depthStencilTexture),e.setRenderTarget(R))}let Se=F[U];Se===void 0&&(Se=new ri,Se.layers.enable(U),Se.viewport=new Zt,F[U]=Se),Se.matrix.fromArray(Me.transform.matrix),Se.matrix.decompose(Se.position,Se.quaternion,Se.scale),Se.projectionMatrix.fromArray(Me.projectionMatrix),Se.projectionMatrixInverse.copy(Se.projectionMatrix).invert(),Se.viewport.set(_e.x,_e.y,_e.width,_e.height),U===0&&($.matrix.copy(Se.matrix),$.matrix.decompose($.position,$.quaternion,$.scale)),ye===!0&&$.cameras.push(Se)}const we=o.enabledFeatures;if(we&&we.includes("depth-sensing")&&o.depthUsage=="gpu-optimized"&&A){g=r.getBinding();const U=g.getDepthInformation(Ee[0]);U&&U.isValid&&U.texture&&y.init(U,o.renderState)}if(we&&we.includes("camera-access")&&A){e.state.unbindTexture(),g=r.getBinding();for(let U=0;U<Ee.length;U++){const Me=Ee[U].camera;if(Me){let _e=x[Me];_e||(_e=new ig,x[Me]=_e);const Se=g.getCameraImage(Me);_e.sourceTexture=Se}}}}for(let Ee=0;Ee<z.length;Ee++){const ye=H[Ee],we=z[Ee];ye!==null&&we!==void 0&&we.update(ye,oe,p||u)}Z&&Z(K,oe),oe.detectedPlanes&&r.dispatchEvent({type:"planesdetected",data:oe}),M=null}const he=new pg;he.setAnimationLoop(ue),this.setAnimationLoop=function(K){Z=K},this.dispose=function(){}}}const Zr=new Ri,Lw=new $t;function Dw(s,e){function t(y,x){y.matrixAutoUpdate===!0&&y.updateMatrix(),x.value.copy(y.matrix)}function r(y,x){x.color.getRGB(y.fogColor.value,Q0(s)),x.isFog?(y.fogNear.value=x.near,y.fogFar.value=x.far):x.isFogExp2&&(y.fogDensity.value=x.density)}function o(y,x,O,D,R){x.isMeshBasicMaterial||x.isMeshLambertMaterial?l(y,x):x.isMeshToonMaterial?(l(y,x),g(y,x)):x.isMeshPhongMaterial?(l(y,x),v(y,x)):x.isMeshStandardMaterial?(l(y,x),_(y,x),x.isMeshPhysicalMaterial&&S(y,x,R)):x.isMeshMatcapMaterial?(l(y,x),M(y,x)):x.isMeshDepthMaterial?l(y,x):x.isMeshDistanceMaterial?(l(y,x),A(y,x)):x.isMeshNormalMaterial?l(y,x):x.isLineBasicMaterial?(u(y,x),x.isLineDashedMaterial&&f(y,x)):x.isPointsMaterial?d(y,x,O,D):x.isSpriteMaterial?p(y,x):x.isShadowMaterial?(y.color.value.copy(x.color),y.opacity.value=x.opacity):x.isShaderMaterial&&(x.uniformsNeedUpdate=!1)}function l(y,x){y.opacity.value=x.opacity,x.color&&y.diffuse.value.copy(x.color),x.emissive&&y.emissive.value.copy(x.emissive).multiplyScalar(x.emissiveIntensity),x.map&&(y.map.value=x.map,t(x.map,y.mapTransform)),x.alphaMap&&(y.alphaMap.value=x.alphaMap,t(x.alphaMap,y.alphaMapTransform)),x.bumpMap&&(y.bumpMap.value=x.bumpMap,t(x.bumpMap,y.bumpMapTransform),y.bumpScale.value=x.bumpScale,x.side===Gn&&(y.bumpScale.value*=-1)),x.normalMap&&(y.normalMap.value=x.normalMap,t(x.normalMap,y.normalMapTransform),y.normalScale.value.copy(x.normalScale),x.side===Gn&&y.normalScale.value.negate()),x.displacementMap&&(y.displacementMap.value=x.displacementMap,t(x.displacementMap,y.displacementMapTransform),y.displacementScale.value=x.displacementScale,y.displacementBias.value=x.displacementBias),x.emissiveMap&&(y.emissiveMap.value=x.emissiveMap,t(x.emissiveMap,y.emissiveMapTransform)),x.specularMap&&(y.specularMap.value=x.specularMap,t(x.specularMap,y.specularMapTransform)),x.alphaTest>0&&(y.alphaTest.value=x.alphaTest);const O=e.get(x),D=O.envMap,R=O.envMapRotation;D&&(y.envMap.value=D,Zr.copy(R),Zr.x*=-1,Zr.y*=-1,Zr.z*=-1,D.isCubeTexture&&D.isRenderTargetTexture===!1&&(Zr.y*=-1,Zr.z*=-1),y.envMapRotation.value.setFromMatrix4(Lw.makeRotationFromEuler(Zr)),y.flipEnvMap.value=D.isCubeTexture&&D.isRenderTargetTexture===!1?-1:1,y.reflectivity.value=x.reflectivity,y.ior.value=x.ior,y.refractionRatio.value=x.refractionRatio),x.lightMap&&(y.lightMap.value=x.lightMap,y.lightMapIntensity.value=x.lightMapIntensity,t(x.lightMap,y.lightMapTransform)),x.aoMap&&(y.aoMap.value=x.aoMap,y.aoMapIntensity.value=x.aoMapIntensity,t(x.aoMap,y.aoMapTransform))}function u(y,x){y.diffuse.value.copy(x.color),y.opacity.value=x.opacity,x.map&&(y.map.value=x.map,t(x.map,y.mapTransform))}function f(y,x){y.dashSize.value=x.dashSize,y.totalSize.value=x.dashSize+x.gapSize,y.scale.value=x.scale}function d(y,x,O,D){y.diffuse.value.copy(x.color),y.opacity.value=x.opacity,y.size.value=x.size*O,y.scale.value=D*.5,x.map&&(y.map.value=x.map,t(x.map,y.uvTransform)),x.alphaMap&&(y.alphaMap.value=x.alphaMap,t(x.alphaMap,y.alphaMapTransform)),x.alphaTest>0&&(y.alphaTest.value=x.alphaTest)}function p(y,x){y.diffuse.value.copy(x.color),y.opacity.value=x.opacity,y.rotation.value=x.rotation,x.map&&(y.map.value=x.map,t(x.map,y.mapTransform)),x.alphaMap&&(y.alphaMap.value=x.alphaMap,t(x.alphaMap,y.alphaMapTransform)),x.alphaTest>0&&(y.alphaTest.value=x.alphaTest)}function v(y,x){y.specular.value.copy(x.specular),y.shininess.value=Math.max(x.shininess,1e-4)}function g(y,x){x.gradientMap&&(y.gradientMap.value=x.gradientMap)}function _(y,x){y.metalness.value=x.metalness,x.metalnessMap&&(y.metalnessMap.value=x.metalnessMap,t(x.metalnessMap,y.metalnessMapTransform)),y.roughness.value=x.roughness,x.roughnessMap&&(y.roughnessMap.value=x.roughnessMap,t(x.roughnessMap,y.roughnessMapTransform)),x.envMap&&(y.envMapIntensity.value=x.envMapIntensity)}function S(y,x,O){y.ior.value=x.ior,x.sheen>0&&(y.sheenColor.value.copy(x.sheenColor).multiplyScalar(x.sheen),y.sheenRoughness.value=x.sheenRoughness,x.sheenColorMap&&(y.sheenColorMap.value=x.sheenColorMap,t(x.sheenColorMap,y.sheenColorMapTransform)),x.sheenRoughnessMap&&(y.sheenRoughnessMap.value=x.sheenRoughnessMap,t(x.sheenRoughnessMap,y.sheenRoughnessMapTransform))),x.clearcoat>0&&(y.clearcoat.value=x.clearcoat,y.clearcoatRoughness.value=x.clearcoatRoughness,x.clearcoatMap&&(y.clearcoatMap.value=x.clearcoatMap,t(x.clearcoatMap,y.clearcoatMapTransform)),x.clearcoatRoughnessMap&&(y.clearcoatRoughnessMap.value=x.clearcoatRoughnessMap,t(x.clearcoatRoughnessMap,y.clearcoatRoughnessMapTransform)),x.clearcoatNormalMap&&(y.clearcoatNormalMap.value=x.clearcoatNormalMap,t(x.clearcoatNormalMap,y.clearcoatNormalMapTransform),y.clearcoatNormalScale.value.copy(x.clearcoatNormalScale),x.side===Gn&&y.clearcoatNormalScale.value.negate())),x.dispersion>0&&(y.dispersion.value=x.dispersion),x.iridescence>0&&(y.iridescence.value=x.iridescence,y.iridescenceIOR.value=x.iridescenceIOR,y.iridescenceThicknessMinimum.value=x.iridescenceThicknessRange[0],y.iridescenceThicknessMaximum.value=x.iridescenceThicknessRange[1],x.iridescenceMap&&(y.iridescenceMap.value=x.iridescenceMap,t(x.iridescenceMap,y.iridescenceMapTransform)),x.iridescenceThicknessMap&&(y.iridescenceThicknessMap.value=x.iridescenceThicknessMap,t(x.iridescenceThicknessMap,y.iridescenceThicknessMapTransform))),x.transmission>0&&(y.transmission.value=x.transmission,y.transmissionSamplerMap.value=O.texture,y.transmissionSamplerSize.value.set(O.width,O.height),x.transmissionMap&&(y.transmissionMap.value=x.transmissionMap,t(x.transmissionMap,y.transmissionMapTransform)),y.thickness.value=x.thickness,x.thicknessMap&&(y.thicknessMap.value=x.thicknessMap,t(x.thicknessMap,y.thicknessMapTransform)),y.attenuationDistance.value=x.attenuationDistance,y.attenuationColor.value.copy(x.attenuationColor)),x.anisotropy>0&&(y.anisotropyVector.value.set(x.anisotropy*Math.cos(x.anisotropyRotation),x.anisotropy*Math.sin(x.anisotropyRotation)),x.anisotropyMap&&(y.anisotropyMap.value=x.anisotropyMap,t(x.anisotropyMap,y.anisotropyMapTransform))),y.specularIntensity.value=x.specularIntensity,y.specularColor.value.copy(x.specularColor),x.specularColorMap&&(y.specularColorMap.value=x.specularColorMap,t(x.specularColorMap,y.specularColorMapTransform)),x.specularIntensityMap&&(y.specularIntensityMap.value=x.specularIntensityMap,t(x.specularIntensityMap,y.specularIntensityMapTransform))}function M(y,x){x.matcap&&(y.matcap.value=x.matcap)}function A(y,x){const O=e.get(x).light;y.referencePosition.value.setFromMatrixPosition(O.matrixWorld),y.nearDistance.value=O.shadow.camera.near,y.farDistance.value=O.shadow.camera.far}return{refreshFogUniforms:r,refreshMaterialUniforms:o}}function Nw(s,e,t,r){let o={},l={},u=[];const f=s.getParameter(s.MAX_UNIFORM_BUFFER_BINDINGS);function d(O,D){const R=D.program;r.uniformBlockBinding(O,R)}function p(O,D){let R=o[O.id];R===void 0&&(M(O),R=v(O),o[O.id]=R,O.addEventListener("dispose",y));const z=D.program;r.updateUBOMapping(O,z);const H=e.render.frame;l[O.id]!==H&&(_(O),l[O.id]=H)}function v(O){const D=g();O.__bindingPointIndex=D;const R=s.createBuffer(),z=O.__size,H=O.usage;return s.bindBuffer(s.UNIFORM_BUFFER,R),s.bufferData(s.UNIFORM_BUFFER,z,H),s.bindBuffer(s.UNIFORM_BUFFER,null),s.bindBufferBase(s.UNIFORM_BUFFER,D,R),R}function g(){for(let O=0;O<f;O++)if(u.indexOf(O)===-1)return u.push(O),O;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function _(O){const D=o[O.id],R=O.uniforms,z=O.__cache;s.bindBuffer(s.UNIFORM_BUFFER,D);for(let H=0,I=R.length;H<I;H++){const N=Array.isArray(R[H])?R[H]:[R[H]];for(let C=0,T=N.length;C<T;C++){const F=N[C];if(S(F,H,C,z)===!0){const $=F.__offset,ee=Array.isArray(F.value)?F.value:[F.value];let le=0;for(let ne=0;ne<ee.length;ne++){const ce=ee[ne],re=A(ce);typeof ce=="number"||typeof ce=="boolean"?(F.__data[0]=ce,s.bufferSubData(s.UNIFORM_BUFFER,$+le,F.__data)):ce.isMatrix3?(F.__data[0]=ce.elements[0],F.__data[1]=ce.elements[1],F.__data[2]=ce.elements[2],F.__data[3]=0,F.__data[4]=ce.elements[3],F.__data[5]=ce.elements[4],F.__data[6]=ce.elements[5],F.__data[7]=0,F.__data[8]=ce.elements[6],F.__data[9]=ce.elements[7],F.__data[10]=ce.elements[8],F.__data[11]=0):(ce.toArray(F.__data,le),le+=re.storage/Float32Array.BYTES_PER_ELEMENT)}s.bufferSubData(s.UNIFORM_BUFFER,$,F.__data)}}}s.bindBuffer(s.UNIFORM_BUFFER,null)}function S(O,D,R,z){const H=O.value,I=D+"_"+R;if(z[I]===void 0)return typeof H=="number"||typeof H=="boolean"?z[I]=H:z[I]=H.clone(),!0;{const N=z[I];if(typeof H=="number"||typeof H=="boolean"){if(N!==H)return z[I]=H,!0}else if(N.equals(H)===!1)return N.copy(H),!0}return!1}function M(O){const D=O.uniforms;let R=0;const z=16;for(let I=0,N=D.length;I<N;I++){const C=Array.isArray(D[I])?D[I]:[D[I]];for(let T=0,F=C.length;T<F;T++){const $=C[T],ee=Array.isArray($.value)?$.value:[$.value];for(let le=0,ne=ee.length;le<ne;le++){const ce=ee[le],re=A(ce),V=R%z,me=V%re.boundary,ie=V+me;R+=me,ie!==0&&z-ie<re.storage&&(R+=z-ie),$.__data=new Float32Array(re.storage/Float32Array.BYTES_PER_ELEMENT),$.__offset=R,R+=re.storage}}}const H=R%z;return H>0&&(R+=z-H),O.__size=R,O.__cache={},this}function A(O){const D={boundary:0,storage:0};return typeof O=="number"||typeof O=="boolean"?(D.boundary=4,D.storage=4):O.isVector2?(D.boundary=8,D.storage=8):O.isVector3||O.isColor?(D.boundary=16,D.storage=12):O.isVector4?(D.boundary=16,D.storage=16):O.isMatrix3?(D.boundary=48,D.storage=48):O.isMatrix4?(D.boundary=64,D.storage=64):O.isTexture?console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group."):console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",O),D}function y(O){const D=O.target;D.removeEventListener("dispose",y);const R=u.indexOf(D.__bindingPointIndex);u.splice(R,1),s.deleteBuffer(o[D.id]),delete o[D.id],delete l[D.id]}function x(){for(const O in o)s.deleteBuffer(o[O]);u=[],o={},l={}}return{bind:d,update:p,dispose:x}}class Iw{constructor(e={}){const{canvas:t=Ix(),context:r=null,depth:o=!0,stencil:l=!1,alpha:u=!1,antialias:f=!1,premultipliedAlpha:d=!0,preserveDrawingBuffer:p=!1,powerPreference:v="default",failIfMajorPerformanceCaveat:g=!1,reversedDepthBuffer:_=!1}=e;this.isWebGLRenderer=!0;let S;if(r!==null){if(typeof WebGLRenderingContext<"u"&&r instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");S=r.getContextAttributes().alpha}else S=u;const M=new Uint32Array(4),A=new Int32Array(4);let y=null,x=null;const O=[],D=[];this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Rr,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const R=this;let z=!1;this._outputColorSpace=Vn;let H=0,I=0,N=null,C=-1,T=null;const F=new Zt,$=new Zt;let ee=null;const le=new It(0);let ne=0,ce=t.width,re=t.height,V=1,me=null,ie=null;const P=new Zt(0,0,ce,re),B=new Zt(0,0,ce,re);let Z=!1;const ue=new Cd;let he=!1,K=!1;const oe=new $t,Ee=new Q,ye=new Zt,we={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let tt=!1;function at(){return N===null?V:1}let U=r;function Me(b,j){return t.getContext(b,j)}try{const b={alpha:!0,depth:o,stencil:l,antialias:f,premultipliedAlpha:d,preserveDrawingBuffer:p,powerPreference:v,failIfMajorPerformanceCaveat:g};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${_d}`),t.addEventListener("webglcontextlost",ke,!1),t.addEventListener("webglcontextrestored",Xe,!1),t.addEventListener("webglcontextcreationerror",De,!1),U===null){const j="webgl2";if(U=Me(j,b),U===null)throw Me(j)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(b){throw console.error("THREE.WebGLRenderer: "+b.message),b}let _e,Se,fe,be,xe,Re,ct,ft,L,w,J,ge,Ae,ve,Je,Le,Ke,nt,Ie,He,ut,Ze,Ve,ht;function X(){_e=new WM(U),_e.init(),Ze=new Aw(U,_e),Se=new OM(U,_e,e,Ze),fe=new ww(U,_e),Se.reversedDepthBuffer&&_&&fe.buffers.depth.setReversed(!0),be=new qM(U),xe=new fw,Re=new Tw(U,_e,fe,xe,Se,Ze,be),ct=new BM(R),ft=new GM(R),L=new Qy(U),Ve=new UM(U,L),w=new XM(U,L,be,Ve),J=new $M(U,w,L,be),Ie=new YM(U,Se,Re),Le=new kM(xe),ge=new uw(R,ct,ft,_e,Se,Ve,Le),Ae=new Dw(R,xe),ve=new hw,Je=new xw(_e),nt=new IM(R,ct,ft,fe,J,S,d),Ke=new Mw(R,J,Se),ht=new Nw(U,be,Se,fe),He=new FM(U,_e,be),ut=new jM(U,_e,be),be.programs=ge.programs,R.capabilities=Se,R.extensions=_e,R.properties=xe,R.renderLists=ve,R.shadowMap=Ke,R.state=fe,R.info=be}X();const Ue=new Pw(R,U);this.xr=Ue,this.getContext=function(){return U},this.getContextAttributes=function(){return U.getContextAttributes()},this.forceContextLoss=function(){const b=_e.get("WEBGL_lose_context");b&&b.loseContext()},this.forceContextRestore=function(){const b=_e.get("WEBGL_lose_context");b&&b.restoreContext()},this.getPixelRatio=function(){return V},this.setPixelRatio=function(b){b!==void 0&&(V=b,this.setSize(ce,re,!1))},this.getSize=function(b){return b.set(ce,re)},this.setSize=function(b,j,ae=!0){if(Ue.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}ce=b,re=j,t.width=Math.floor(b*V),t.height=Math.floor(j*V),ae===!0&&(t.style.width=b+"px",t.style.height=j+"px"),this.setViewport(0,0,b,j)},this.getDrawingBufferSize=function(b){return b.set(ce*V,re*V).floor()},this.setDrawingBufferSize=function(b,j,ae){ce=b,re=j,V=ae,t.width=Math.floor(b*ae),t.height=Math.floor(j*ae),this.setViewport(0,0,b,j)},this.getCurrentViewport=function(b){return b.copy(F)},this.getViewport=function(b){return b.copy(P)},this.setViewport=function(b,j,ae,pe){b.isVector4?P.set(b.x,b.y,b.z,b.w):P.set(b,j,ae,pe),fe.viewport(F.copy(P).multiplyScalar(V).round())},this.getScissor=function(b){return b.copy(B)},this.setScissor=function(b,j,ae,pe){b.isVector4?B.set(b.x,b.y,b.z,b.w):B.set(b,j,ae,pe),fe.scissor($.copy(B).multiplyScalar(V).round())},this.getScissorTest=function(){return Z},this.setScissorTest=function(b){fe.setScissorTest(Z=b)},this.setOpaqueSort=function(b){me=b},this.setTransparentSort=function(b){ie=b},this.getClearColor=function(b){return b.copy(nt.getClearColor())},this.setClearColor=function(){nt.setClearColor(...arguments)},this.getClearAlpha=function(){return nt.getClearAlpha()},this.setClearAlpha=function(){nt.setClearAlpha(...arguments)},this.clear=function(b=!0,j=!0,ae=!0){let pe=0;if(b){let Y=!1;if(N!==null){const Be=N.texture.format;Y=Be===wd||Be===Ed||Be===Md}if(Y){const Be=N.texture.type,We=Be===Ai||Be===ss||Be===Jo||Be===Qo||Be===yd||Be===Sd,it=nt.getClearColor(),Ye=nt.getClearAlpha(),gt=it.r,_t=it.g,lt=it.b;We?(M[0]=gt,M[1]=_t,M[2]=lt,M[3]=Ye,U.clearBufferuiv(U.COLOR,0,M)):(A[0]=gt,A[1]=_t,A[2]=lt,A[3]=Ye,U.clearBufferiv(U.COLOR,0,A))}else pe|=U.COLOR_BUFFER_BIT}j&&(pe|=U.DEPTH_BUFFER_BIT),ae&&(pe|=U.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),U.clear(pe)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){t.removeEventListener("webglcontextlost",ke,!1),t.removeEventListener("webglcontextrestored",Xe,!1),t.removeEventListener("webglcontextcreationerror",De,!1),nt.dispose(),ve.dispose(),Je.dispose(),xe.dispose(),ct.dispose(),ft.dispose(),J.dispose(),Ve.dispose(),ht.dispose(),ge.dispose(),Ue.dispose(),Ue.removeEventListener("sessionstart",vt),Ue.removeEventListener("sessionend",Lt),Wt.stop()};function ke(b){b.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),z=!0}function Xe(){console.log("THREE.WebGLRenderer: Context Restored."),z=!1;const b=be.autoReset,j=Ke.enabled,ae=Ke.autoUpdate,pe=Ke.needsUpdate,Y=Ke.type;X(),be.autoReset=b,Ke.enabled=j,Ke.autoUpdate=ae,Ke.needsUpdate=pe,Ke.type=Y}function De(b){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",b.statusMessage)}function Te(b){const j=b.target;j.removeEventListener("dispose",Te),et(j)}function et(b){xt(b),xe.remove(b)}function xt(b){const j=xe.get(b).programs;j!==void 0&&(j.forEach(function(ae){ge.releaseProgram(ae)}),b.isShaderMaterial&&ge.releaseShaderCache(b))}this.renderBufferDirect=function(b,j,ae,pe,Y,Be){j===null&&(j=we);const We=Y.isMesh&&Y.matrixWorld.determinant()<0,it=Wn(b,j,ae,pe,Y);fe.setMaterial(pe,We);let Ye=ae.index,gt=1;if(pe.wireframe===!0){if(Ye=w.getWireframeAttribute(ae),Ye===void 0)return;gt=2}const _t=ae.drawRange,lt=ae.attributes.position;let yt=_t.start*gt,Ut=(_t.start+_t.count)*gt;Be!==null&&(yt=Math.max(yt,Be.start*gt),Ut=Math.min(Ut,(Be.start+Be.count)*gt)),Ye!==null?(yt=Math.max(yt,0),Ut=Math.min(Ut,Ye.count)):lt!=null&&(yt=Math.max(yt,0),Ut=Math.min(Ut,lt.count));const bt=Ut-yt;if(bt<0||bt===1/0)return;Ve.setup(Y,pe,it,ae,Ye);let Bt,Ft=He;if(Ye!==null&&(Bt=L.get(Ye),Ft=ut,Ft.setIndex(Bt)),Y.isMesh)pe.wireframe===!0?(fe.setLineWidth(pe.wireframeLinewidth*at()),Ft.setMode(U.LINES)):Ft.setMode(U.TRIANGLES);else if(Y.isLine){let dt=pe.linewidth;dt===void 0&&(dt=1),fe.setLineWidth(dt*at()),Y.isLineSegments?Ft.setMode(U.LINES):Y.isLineLoop?Ft.setMode(U.LINE_LOOP):Ft.setMode(U.LINE_STRIP)}else Y.isPoints?Ft.setMode(U.POINTS):Y.isSprite&&Ft.setMode(U.TRIANGLES);if(Y.isBatchedMesh)if(Y._multiDrawInstances!==null)na("THREE.WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),Ft.renderMultiDrawInstances(Y._multiDrawStarts,Y._multiDrawCounts,Y._multiDrawCount,Y._multiDrawInstances);else if(_e.get("WEBGL_multi_draw"))Ft.renderMultiDraw(Y._multiDrawStarts,Y._multiDrawCounts,Y._multiDrawCount);else{const dt=Y._multiDrawStarts,Ot=Y._multiDrawCounts,At=Y._multiDrawCount,rn=Ye?L.get(Ye).bytesPerElement:1,si=xe.get(pe).currentProgram.getUniforms();for(let Cn=0;Cn<At;Cn++)si.setValue(U,"_gl_DrawID",Cn),Ft.render(dt[Cn]/rn,Ot[Cn])}else if(Y.isInstancedMesh)Ft.renderInstances(yt,bt,Y.count);else if(ae.isInstancedBufferGeometry){const dt=ae._maxInstanceCount!==void 0?ae._maxInstanceCount:1/0,Ot=Math.min(ae.instanceCount,dt);Ft.renderInstances(yt,bt,Ot)}else Ft.render(yt,bt)};function Ne(b,j,ae){b.transparent===!0&&b.side===Wi&&b.forceSinglePass===!1?(b.side=Gn,b.needsUpdate=!0,Ki(b,j,ae),b.side=Cr,b.needsUpdate=!0,Ki(b,j,ae),b.side=Wi):Ki(b,j,ae)}this.compile=function(b,j,ae=null){ae===null&&(ae=b),x=Je.get(ae),x.init(j),D.push(x),ae.traverseVisible(function(Y){Y.isLight&&Y.layers.test(j.layers)&&(x.pushLight(Y),Y.castShadow&&x.pushShadow(Y))}),b!==ae&&b.traverseVisible(function(Y){Y.isLight&&Y.layers.test(j.layers)&&(x.pushLight(Y),Y.castShadow&&x.pushShadow(Y))}),x.setupLights();const pe=new Set;return b.traverse(function(Y){if(!(Y.isMesh||Y.isPoints||Y.isLine||Y.isSprite))return;const Be=Y.material;if(Be)if(Array.isArray(Be))for(let We=0;We<Be.length;We++){const it=Be[We];Ne(it,ae,Y),pe.add(it)}else Ne(Be,ae,Y),pe.add(Be)}),x=D.pop(),pe},this.compileAsync=function(b,j,ae=null){const pe=this.compile(b,j,ae);return new Promise(Y=>{function Be(){if(pe.forEach(function(We){xe.get(We).currentProgram.isReady()&&pe.delete(We)}),pe.size===0){Y(b);return}setTimeout(Be,10)}_e.get("KHR_parallel_shader_compile")!==null?Be():setTimeout(Be,10)})};let qe=null;function Mt(b){qe&&qe(b)}function vt(){Wt.stop()}function Lt(){Wt.start()}const Wt=new pg;Wt.setAnimationLoop(Mt),typeof self<"u"&&Wt.setContext(self),this.setAnimationLoop=function(b){qe=b,Ue.setAnimationLoop(b),b===null?Wt.stop():Wt.start()},Ue.addEventListener("sessionstart",vt),Ue.addEventListener("sessionend",Lt),this.render=function(b,j){if(j!==void 0&&j.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(z===!0)return;if(b.matrixWorldAutoUpdate===!0&&b.updateMatrixWorld(),j.parent===null&&j.matrixWorldAutoUpdate===!0&&j.updateMatrixWorld(),Ue.enabled===!0&&Ue.isPresenting===!0&&(Ue.cameraAutoUpdate===!0&&Ue.updateCamera(j),j=Ue.getCamera()),b.isScene===!0&&b.onBeforeRender(R,b,j,N),x=Je.get(b,D.length),x.init(j),D.push(x),oe.multiplyMatrices(j.projectionMatrix,j.matrixWorldInverse),ue.setFromProjectionMatrix(oe,wi,j.reversedDepth),K=this.localClippingEnabled,he=Le.init(this.clippingPlanes,K),y=ve.get(b,O.length),y.init(),O.push(y),Ue.enabled===!0&&Ue.isPresenting===!0){const Be=R.xr.getDepthSensingMesh();Be!==null&&xn(Be,j,-1/0,R.sortObjects)}xn(b,j,0,R.sortObjects),y.finish(),R.sortObjects===!0&&y.sort(me,ie),tt=Ue.enabled===!1||Ue.isPresenting===!1||Ue.hasDepthSensing()===!1,tt&&nt.addToRenderList(y,b),this.info.render.frame++,he===!0&&Le.beginShadows();const ae=x.state.shadowsArray;Ke.render(ae,b,j),he===!0&&Le.endShadows(),this.info.autoReset===!0&&this.info.reset();const pe=y.opaque,Y=y.transmissive;if(x.setupLights(),j.isArrayCamera){const Be=j.cameras;if(Y.length>0)for(let We=0,it=Be.length;We<it;We++){const Ye=Be[We];fn(pe,Y,b,Ye)}tt&&nt.render(b);for(let We=0,it=Be.length;We<it;We++){const Ye=Be[We];un(y,b,Ye,Ye.viewport)}}else Y.length>0&&fn(pe,Y,b,j),tt&&nt.render(b),un(y,b,j);N!==null&&I===0&&(Re.updateMultisampleRenderTarget(N),Re.updateRenderTargetMipmap(N)),b.isScene===!0&&b.onAfterRender(R,b,j),Ve.resetDefaultState(),C=-1,T=null,D.pop(),D.length>0?(x=D[D.length-1],he===!0&&Le.setGlobalState(R.clippingPlanes,x.state.camera)):x=null,O.pop(),O.length>0?y=O[O.length-1]:y=null};function xn(b,j,ae,pe){if(b.visible===!1)return;if(b.layers.test(j.layers)){if(b.isGroup)ae=b.renderOrder;else if(b.isLOD)b.autoUpdate===!0&&b.update(j);else if(b.isLight)x.pushLight(b),b.castShadow&&x.pushShadow(b);else if(b.isSprite){if(!b.frustumCulled||ue.intersectsSprite(b)){pe&&ye.setFromMatrixPosition(b.matrixWorld).applyMatrix4(oe);const We=J.update(b),it=b.material;it.visible&&y.push(b,We,it,ae,ye.z,null)}}else if((b.isMesh||b.isLine||b.isPoints)&&(!b.frustumCulled||ue.intersectsObject(b))){const We=J.update(b),it=b.material;if(pe&&(b.boundingSphere!==void 0?(b.boundingSphere===null&&b.computeBoundingSphere(),ye.copy(b.boundingSphere.center)):(We.boundingSphere===null&&We.computeBoundingSphere(),ye.copy(We.boundingSphere.center)),ye.applyMatrix4(b.matrixWorld).applyMatrix4(oe)),Array.isArray(it)){const Ye=We.groups;for(let gt=0,_t=Ye.length;gt<_t;gt++){const lt=Ye[gt],yt=it[lt.materialIndex];yt&&yt.visible&&y.push(b,We,yt,ae,ye.z,lt)}}else it.visible&&y.push(b,We,it,ae,ye.z,null)}}const Be=b.children;for(let We=0,it=Be.length;We<it;We++)xn(Be[We],j,ae,pe)}function un(b,j,ae,pe){const Y=b.opaque,Be=b.transmissive,We=b.transparent;x.setupLightsView(ae),he===!0&&Le.setGlobalState(R.clippingPlanes,ae),pe&&fe.viewport(F.copy(pe)),Y.length>0&&Jt(Y,j,ae),Be.length>0&&Jt(Be,j,ae),We.length>0&&Jt(We,j,ae),fe.buffers.depth.setTest(!0),fe.buffers.depth.setMask(!0),fe.buffers.color.setMask(!0),fe.setPolygonOffset(!1)}function fn(b,j,ae,pe){if((ae.isScene===!0?ae.overrideMaterial:null)!==null)return;x.state.transmissionRenderTarget[pe.id]===void 0&&(x.state.transmissionRenderTarget[pe.id]=new os(1,1,{generateMipmaps:!0,type:_e.has("EXT_color_buffer_half_float")||_e.has("EXT_color_buffer_float")?oa:Ai,minFilter:rs,samples:4,stencilBuffer:l,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:Nt.workingColorSpace}));const Be=x.state.transmissionRenderTarget[pe.id],We=pe.viewport||F;Be.setSize(We.z*R.transmissionResolutionScale,We.w*R.transmissionResolutionScale);const it=R.getRenderTarget(),Ye=R.getActiveCubeFace(),gt=R.getActiveMipmapLevel();R.setRenderTarget(Be),R.getClearColor(le),ne=R.getClearAlpha(),ne<1&&R.setClearColor(16777215,.5),R.clear(),tt&&nt.render(ae);const _t=R.toneMapping;R.toneMapping=Rr;const lt=pe.viewport;if(pe.viewport!==void 0&&(pe.viewport=void 0),x.setupLightsView(pe),he===!0&&Le.setGlobalState(R.clippingPlanes,pe),Jt(b,ae,pe),Re.updateMultisampleRenderTarget(Be),Re.updateRenderTargetMipmap(Be),_e.has("WEBGL_multisampled_render_to_texture")===!1){let yt=!1;for(let Ut=0,bt=j.length;Ut<bt;Ut++){const Bt=j[Ut],Ft=Bt.object,dt=Bt.geometry,Ot=Bt.material,At=Bt.group;if(Ot.side===Wi&&Ft.layers.test(pe.layers)){const rn=Ot.side;Ot.side=Gn,Ot.needsUpdate=!0,$i(Ft,ae,pe,dt,Ot,At),Ot.side=rn,Ot.needsUpdate=!0,yt=!0}}yt===!0&&(Re.updateMultisampleRenderTarget(Be),Re.updateRenderTargetMipmap(Be))}R.setRenderTarget(it,Ye,gt),R.setClearColor(le,ne),lt!==void 0&&(pe.viewport=lt),R.toneMapping=_t}function Jt(b,j,ae){const pe=j.isScene===!0?j.overrideMaterial:null;for(let Y=0,Be=b.length;Y<Be;Y++){const We=b[Y],it=We.object,Ye=We.geometry,gt=We.group;let _t=We.material;_t.allowOverride===!0&&pe!==null&&(_t=pe),it.layers.test(ae.layers)&&$i(it,j,ae,Ye,_t,gt)}}function $i(b,j,ae,pe,Y,Be){b.onBeforeRender(R,j,ae,pe,Y,Be),b.modelViewMatrix.multiplyMatrices(ae.matrixWorldInverse,b.matrixWorld),b.normalMatrix.getNormalMatrix(b.modelViewMatrix),Y.onBeforeRender(R,j,ae,pe,b,Be),Y.transparent===!0&&Y.side===Wi&&Y.forceSinglePass===!1?(Y.side=Gn,Y.needsUpdate=!0,R.renderBufferDirect(ae,j,pe,Y,b,Be),Y.side=Cr,Y.needsUpdate=!0,R.renderBufferDirect(ae,j,pe,Y,b,Be),Y.side=Wi):R.renderBufferDirect(ae,j,pe,Y,b,Be),b.onAfterRender(R,j,ae,pe,Y,Be)}function Ki(b,j,ae){j.isScene!==!0&&(j=we);const pe=xe.get(b),Y=x.state.lights,Be=x.state.shadowsArray,We=Y.state.version,it=ge.getParameters(b,Y.state,Be,j,ae),Ye=ge.getProgramCacheKey(it);let gt=pe.programs;pe.environment=b.isMeshStandardMaterial?j.environment:null,pe.fog=j.fog,pe.envMap=(b.isMeshStandardMaterial?ft:ct).get(b.envMap||pe.environment),pe.envMapRotation=pe.environment!==null&&b.envMap===null?j.environmentRotation:b.envMapRotation,gt===void 0&&(b.addEventListener("dispose",Te),gt=new Map,pe.programs=gt);let _t=gt.get(Ye);if(_t!==void 0){if(pe.currentProgram===_t&&pe.lightsStateVersion===We)return ls(b,it),_t}else it.uniforms=ge.getUniforms(b),b.onBeforeCompile(it,R),_t=ge.acquireProgram(it,Ye),gt.set(Ye,_t),pe.uniforms=it.uniforms;const lt=pe.uniforms;return(!b.isShaderMaterial&&!b.isRawShaderMaterial||b.clipping===!0)&&(lt.clippingPlanes=Le.uniform),ls(b,it),pe.needsLights=Qi(b),pe.lightsStateVersion=We,pe.needsLights&&(lt.ambientLightColor.value=Y.state.ambient,lt.lightProbe.value=Y.state.probe,lt.directionalLights.value=Y.state.directional,lt.directionalLightShadows.value=Y.state.directionalShadow,lt.spotLights.value=Y.state.spot,lt.spotLightShadows.value=Y.state.spotShadow,lt.rectAreaLights.value=Y.state.rectArea,lt.ltc_1.value=Y.state.rectAreaLTC1,lt.ltc_2.value=Y.state.rectAreaLTC2,lt.pointLights.value=Y.state.point,lt.pointLightShadows.value=Y.state.pointShadow,lt.hemisphereLights.value=Y.state.hemi,lt.directionalShadowMap.value=Y.state.directionalShadowMap,lt.directionalShadowMatrix.value=Y.state.directionalShadowMatrix,lt.spotShadowMap.value=Y.state.spotShadowMap,lt.spotLightMatrix.value=Y.state.spotLightMatrix,lt.spotLightMap.value=Y.state.spotLightMap,lt.pointShadowMap.value=Y.state.pointShadowMap,lt.pointShadowMatrix.value=Y.state.pointShadowMatrix),pe.currentProgram=_t,pe.uniformsList=null,_t}function Zi(b){if(b.uniformsList===null){const j=b.currentProgram.getUniforms();b.uniformsList=ql.seqWithValue(j.seq,b.uniforms)}return b.uniformsList}function ls(b,j){const ae=xe.get(b);ae.outputColorSpace=j.outputColorSpace,ae.batching=j.batching,ae.batchingColor=j.batchingColor,ae.instancing=j.instancing,ae.instancingColor=j.instancingColor,ae.instancingMorph=j.instancingMorph,ae.skinning=j.skinning,ae.morphTargets=j.morphTargets,ae.morphNormals=j.morphNormals,ae.morphColors=j.morphColors,ae.morphTargetsCount=j.morphTargetsCount,ae.numClippingPlanes=j.numClippingPlanes,ae.numIntersection=j.numClipIntersection,ae.vertexAlphas=j.vertexAlphas,ae.vertexTangents=j.vertexTangents,ae.toneMapping=j.toneMapping}function Wn(b,j,ae,pe,Y){j.isScene!==!0&&(j=we),Re.resetTextureUnits();const Be=j.fog,We=pe.isMeshStandardMaterial?j.environment:null,it=N===null?R.outputColorSpace:N.isXRRenderTarget===!0?N.texture.colorSpace:to,Ye=(pe.isMeshStandardMaterial?ft:ct).get(pe.envMap||We),gt=pe.vertexColors===!0&&!!ae.attributes.color&&ae.attributes.color.itemSize===4,_t=!!ae.attributes.tangent&&(!!pe.normalMap||pe.anisotropy>0),lt=!!ae.morphAttributes.position,yt=!!ae.morphAttributes.normal,Ut=!!ae.morphAttributes.color;let bt=Rr;pe.toneMapped&&(N===null||N.isXRRenderTarget===!0)&&(bt=R.toneMapping);const Bt=ae.morphAttributes.position||ae.morphAttributes.normal||ae.morphAttributes.color,Ft=Bt!==void 0?Bt.length:0,dt=xe.get(pe),Ot=x.state.lights;if(he===!0&&(K===!0||b!==T)){const Qt=b===T&&pe.id===C;Le.setState(pe,b,Qt)}let At=!1;pe.version===dt.__version?(dt.needsLights&&dt.lightsStateVersion!==Ot.state.version||dt.outputColorSpace!==it||Y.isBatchedMesh&&dt.batching===!1||!Y.isBatchedMesh&&dt.batching===!0||Y.isBatchedMesh&&dt.batchingColor===!0&&Y.colorTexture===null||Y.isBatchedMesh&&dt.batchingColor===!1&&Y.colorTexture!==null||Y.isInstancedMesh&&dt.instancing===!1||!Y.isInstancedMesh&&dt.instancing===!0||Y.isSkinnedMesh&&dt.skinning===!1||!Y.isSkinnedMesh&&dt.skinning===!0||Y.isInstancedMesh&&dt.instancingColor===!0&&Y.instanceColor===null||Y.isInstancedMesh&&dt.instancingColor===!1&&Y.instanceColor!==null||Y.isInstancedMesh&&dt.instancingMorph===!0&&Y.morphTexture===null||Y.isInstancedMesh&&dt.instancingMorph===!1&&Y.morphTexture!==null||dt.envMap!==Ye||pe.fog===!0&&dt.fog!==Be||dt.numClippingPlanes!==void 0&&(dt.numClippingPlanes!==Le.numPlanes||dt.numIntersection!==Le.numIntersection)||dt.vertexAlphas!==gt||dt.vertexTangents!==_t||dt.morphTargets!==lt||dt.morphNormals!==yt||dt.morphColors!==Ut||dt.toneMapping!==bt||dt.morphTargetsCount!==Ft)&&(At=!0):(At=!0,dt.__version=pe.version);let rn=dt.currentProgram;At===!0&&(rn=Ki(pe,j,Y));let si=!1,Cn=!1,Dr=!1;const zt=rn.getUniforms(),bn=dt.uniforms;if(fe.useProgram(rn.program)&&(si=!0,Cn=!0,Dr=!0),pe.id!==C&&(C=pe.id,Cn=!0),si||T!==b){fe.buffers.depth.getReversed()&&b.reversedDepth!==!0&&(b._reversedDepth=!0,b.updateProjectionMatrix()),zt.setValue(U,"projectionMatrix",b.projectionMatrix),zt.setValue(U,"viewMatrix",b.matrixWorldInverse);const Sn=zt.map.cameraPosition;Sn!==void 0&&Sn.setValue(U,Ee.setFromMatrixPosition(b.matrixWorld)),Se.logarithmicDepthBuffer&&zt.setValue(U,"logDepthBufFC",2/(Math.log(b.far+1)/Math.LN2)),(pe.isMeshPhongMaterial||pe.isMeshToonMaterial||pe.isMeshLambertMaterial||pe.isMeshBasicMaterial||pe.isMeshStandardMaterial||pe.isShaderMaterial)&&zt.setValue(U,"isOrthographic",b.isOrthographicCamera===!0),T!==b&&(T=b,Cn=!0,Dr=!0)}if(Y.isSkinnedMesh){zt.setOptional(U,Y,"bindMatrix"),zt.setOptional(U,Y,"bindMatrixInverse");const Qt=Y.skeleton;Qt&&(Qt.boneTexture===null&&Qt.computeBoneTexture(),zt.setValue(U,"boneTexture",Qt.boneTexture,Re))}Y.isBatchedMesh&&(zt.setOptional(U,Y,"batchingTexture"),zt.setValue(U,"batchingTexture",Y._matricesTexture,Re),zt.setOptional(U,Y,"batchingIdTexture"),zt.setValue(U,"batchingIdTexture",Y._indirectTexture,Re),zt.setOptional(U,Y,"batchingColorTexture"),Y._colorsTexture!==null&&zt.setValue(U,"batchingColorTexture",Y._colorsTexture,Re));const yn=ae.morphAttributes;if((yn.position!==void 0||yn.normal!==void 0||yn.color!==void 0)&&Ie.update(Y,ae,rn),(Cn||dt.receiveShadow!==Y.receiveShadow)&&(dt.receiveShadow=Y.receiveShadow,zt.setValue(U,"receiveShadow",Y.receiveShadow)),pe.isMeshGouraudMaterial&&pe.envMap!==null&&(bn.envMap.value=Ye,bn.flipEnvMap.value=Ye.isCubeTexture&&Ye.isRenderTargetTexture===!1?-1:1),pe.isMeshStandardMaterial&&pe.envMap===null&&j.environment!==null&&(bn.envMapIntensity.value=j.environmentIntensity),Cn&&(zt.setValue(U,"toneMappingExposure",R.toneMappingExposure),dt.needsLights&&Ji(bn,Dr),Be&&pe.fog===!0&&Ae.refreshFogUniforms(bn,Be),Ae.refreshMaterialUniforms(bn,pe,V,re,x.state.transmissionRenderTarget[b.id]),ql.upload(U,Zi(dt),bn,Re)),pe.isShaderMaterial&&pe.uniformsNeedUpdate===!0&&(ql.upload(U,Zi(dt),bn,Re),pe.uniformsNeedUpdate=!1),pe.isSpriteMaterial&&zt.setValue(U,"center",Y.center),zt.setValue(U,"modelViewMatrix",Y.modelViewMatrix),zt.setValue(U,"normalMatrix",Y.normalMatrix),zt.setValue(U,"modelMatrix",Y.matrixWorld),pe.isShaderMaterial||pe.isRawShaderMaterial){const Qt=pe.uniformsGroups;for(let Sn=0,Nr=Qt.length;Sn<Nr;Sn++){const Rt=Qt[Sn];ht.update(Rt,rn),ht.bind(Rt,rn)}}return rn}function Ji(b,j){b.ambientLightColor.needsUpdate=j,b.lightProbe.needsUpdate=j,b.directionalLights.needsUpdate=j,b.directionalLightShadows.needsUpdate=j,b.pointLights.needsUpdate=j,b.pointLightShadows.needsUpdate=j,b.spotLights.needsUpdate=j,b.spotLightShadows.needsUpdate=j,b.rectAreaLights.needsUpdate=j,b.hemisphereLights.needsUpdate=j}function Qi(b){return b.isMeshLambertMaterial||b.isMeshToonMaterial||b.isMeshPhongMaterial||b.isMeshStandardMaterial||b.isShadowMaterial||b.isShaderMaterial&&b.lights===!0}this.getActiveCubeFace=function(){return H},this.getActiveMipmapLevel=function(){return I},this.getRenderTarget=function(){return N},this.setRenderTargetTextures=function(b,j,ae){const pe=xe.get(b);pe.__autoAllocateDepthBuffer=b.resolveDepthBuffer===!1,pe.__autoAllocateDepthBuffer===!1&&(pe.__useRenderToTexture=!1),xe.get(b.texture).__webglTexture=j,xe.get(b.depthTexture).__webglTexture=pe.__autoAllocateDepthBuffer?void 0:ae,pe.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(b,j){const ae=xe.get(b);ae.__webglFramebuffer=j,ae.__useDefaultFramebuffer=j===void 0};const cs=U.createFramebuffer();this.setRenderTarget=function(b,j=0,ae=0){N=b,H=j,I=ae;let pe=!0,Y=null,Be=!1,We=!1;if(b){const Ye=xe.get(b);if(Ye.__useDefaultFramebuffer!==void 0)fe.bindFramebuffer(U.FRAMEBUFFER,null),pe=!1;else if(Ye.__webglFramebuffer===void 0)Re.setupRenderTarget(b);else if(Ye.__hasExternalTextures)Re.rebindTextures(b,xe.get(b.texture).__webglTexture,xe.get(b.depthTexture).__webglTexture);else if(b.depthBuffer){const lt=b.depthTexture;if(Ye.__boundDepthTexture!==lt){if(lt!==null&&xe.has(lt)&&(b.width!==lt.image.width||b.height!==lt.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");Re.setupDepthRenderbuffer(b)}}const gt=b.texture;(gt.isData3DTexture||gt.isDataArrayTexture||gt.isCompressedArrayTexture)&&(We=!0);const _t=xe.get(b).__webglFramebuffer;b.isWebGLCubeRenderTarget?(Array.isArray(_t[j])?Y=_t[j][ae]:Y=_t[j],Be=!0):b.samples>0&&Re.useMultisampledRTT(b)===!1?Y=xe.get(b).__webglMultisampledFramebuffer:Array.isArray(_t)?Y=_t[ae]:Y=_t,F.copy(b.viewport),$.copy(b.scissor),ee=b.scissorTest}else F.copy(P).multiplyScalar(V).floor(),$.copy(B).multiplyScalar(V).floor(),ee=Z;if(ae!==0&&(Y=cs),fe.bindFramebuffer(U.FRAMEBUFFER,Y)&&pe&&fe.drawBuffers(b,Y),fe.viewport(F),fe.scissor($),fe.setScissorTest(ee),Be){const Ye=xe.get(b.texture);U.framebufferTexture2D(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_CUBE_MAP_POSITIVE_X+j,Ye.__webglTexture,ae)}else if(We){const Ye=j;for(let gt=0;gt<b.textures.length;gt++){const _t=xe.get(b.textures[gt]);U.framebufferTextureLayer(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0+gt,_t.__webglTexture,ae,Ye)}}else if(b!==null&&ae!==0){const Ye=xe.get(b.texture);U.framebufferTexture2D(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,Ye.__webglTexture,ae)}C=-1},this.readRenderTargetPixels=function(b,j,ae,pe,Y,Be,We,it=0){if(!(b&&b.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Ye=xe.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&We!==void 0&&(Ye=Ye[We]),Ye){fe.bindFramebuffer(U.FRAMEBUFFER,Ye);try{const gt=b.textures[it],_t=gt.format,lt=gt.type;if(!Se.textureFormatReadable(_t)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!Se.textureTypeReadable(lt)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}j>=0&&j<=b.width-pe&&ae>=0&&ae<=b.height-Y&&(b.textures.length>1&&U.readBuffer(U.COLOR_ATTACHMENT0+it),U.readPixels(j,ae,pe,Y,Ze.convert(_t),Ze.convert(lt),Be))}finally{const gt=N!==null?xe.get(N).__webglFramebuffer:null;fe.bindFramebuffer(U.FRAMEBUFFER,gt)}}},this.readRenderTargetPixelsAsync=async function(b,j,ae,pe,Y,Be,We,it=0){if(!(b&&b.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Ye=xe.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&We!==void 0&&(Ye=Ye[We]),Ye)if(j>=0&&j<=b.width-pe&&ae>=0&&ae<=b.height-Y){fe.bindFramebuffer(U.FRAMEBUFFER,Ye);const gt=b.textures[it],_t=gt.format,lt=gt.type;if(!Se.textureFormatReadable(_t))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!Se.textureTypeReadable(lt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const yt=U.createBuffer();U.bindBuffer(U.PIXEL_PACK_BUFFER,yt),U.bufferData(U.PIXEL_PACK_BUFFER,Be.byteLength,U.STREAM_READ),b.textures.length>1&&U.readBuffer(U.COLOR_ATTACHMENT0+it),U.readPixels(j,ae,pe,Y,Ze.convert(_t),Ze.convert(lt),0);const Ut=N!==null?xe.get(N).__webglFramebuffer:null;fe.bindFramebuffer(U.FRAMEBUFFER,Ut);const bt=U.fenceSync(U.SYNC_GPU_COMMANDS_COMPLETE,0);return U.flush(),await Ux(U,bt,4),U.bindBuffer(U.PIXEL_PACK_BUFFER,yt),U.getBufferSubData(U.PIXEL_PACK_BUFFER,0,Be),U.deleteBuffer(yt),U.deleteSync(bt),Be}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(b,j=null,ae=0){const pe=Math.pow(2,-ae),Y=Math.floor(b.image.width*pe),Be=Math.floor(b.image.height*pe),We=j!==null?j.x:0,it=j!==null?j.y:0;Re.setTexture2D(b,0),U.copyTexSubImage2D(U.TEXTURE_2D,ae,0,0,We,it,Y,Be),fe.unbindTexture()};const Pr=U.createFramebuffer(),Lr=U.createFramebuffer();this.copyTextureToTexture=function(b,j,ae=null,pe=null,Y=0,Be=null){Be===null&&(Y!==0?(na("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),Be=Y,Y=0):Be=0);let We,it,Ye,gt,_t,lt,yt,Ut,bt;const Bt=b.isCompressedTexture?b.mipmaps[Be]:b.image;if(ae!==null)We=ae.max.x-ae.min.x,it=ae.max.y-ae.min.y,Ye=ae.isBox3?ae.max.z-ae.min.z:1,gt=ae.min.x,_t=ae.min.y,lt=ae.isBox3?ae.min.z:0;else{const yn=Math.pow(2,-Y);We=Math.floor(Bt.width*yn),it=Math.floor(Bt.height*yn),b.isDataArrayTexture?Ye=Bt.depth:b.isData3DTexture?Ye=Math.floor(Bt.depth*yn):Ye=1,gt=0,_t=0,lt=0}pe!==null?(yt=pe.x,Ut=pe.y,bt=pe.z):(yt=0,Ut=0,bt=0);const Ft=Ze.convert(j.format),dt=Ze.convert(j.type);let Ot;j.isData3DTexture?(Re.setTexture3D(j,0),Ot=U.TEXTURE_3D):j.isDataArrayTexture||j.isCompressedArrayTexture?(Re.setTexture2DArray(j,0),Ot=U.TEXTURE_2D_ARRAY):(Re.setTexture2D(j,0),Ot=U.TEXTURE_2D),U.pixelStorei(U.UNPACK_FLIP_Y_WEBGL,j.flipY),U.pixelStorei(U.UNPACK_PREMULTIPLY_ALPHA_WEBGL,j.premultiplyAlpha),U.pixelStorei(U.UNPACK_ALIGNMENT,j.unpackAlignment);const At=U.getParameter(U.UNPACK_ROW_LENGTH),rn=U.getParameter(U.UNPACK_IMAGE_HEIGHT),si=U.getParameter(U.UNPACK_SKIP_PIXELS),Cn=U.getParameter(U.UNPACK_SKIP_ROWS),Dr=U.getParameter(U.UNPACK_SKIP_IMAGES);U.pixelStorei(U.UNPACK_ROW_LENGTH,Bt.width),U.pixelStorei(U.UNPACK_IMAGE_HEIGHT,Bt.height),U.pixelStorei(U.UNPACK_SKIP_PIXELS,gt),U.pixelStorei(U.UNPACK_SKIP_ROWS,_t),U.pixelStorei(U.UNPACK_SKIP_IMAGES,lt);const zt=b.isDataArrayTexture||b.isData3DTexture,bn=j.isDataArrayTexture||j.isData3DTexture;if(b.isDepthTexture){const yn=xe.get(b),Qt=xe.get(j),Sn=xe.get(yn.__renderTarget),Nr=xe.get(Qt.__renderTarget);fe.bindFramebuffer(U.READ_FRAMEBUFFER,Sn.__webglFramebuffer),fe.bindFramebuffer(U.DRAW_FRAMEBUFFER,Nr.__webglFramebuffer);for(let Rt=0;Rt<Ye;Rt++)zt&&(U.framebufferTextureLayer(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,xe.get(b).__webglTexture,Y,lt+Rt),U.framebufferTextureLayer(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,xe.get(j).__webglTexture,Be,bt+Rt)),U.blitFramebuffer(gt,_t,We,it,yt,Ut,We,it,U.DEPTH_BUFFER_BIT,U.NEAREST);fe.bindFramebuffer(U.READ_FRAMEBUFFER,null),fe.bindFramebuffer(U.DRAW_FRAMEBUFFER,null)}else if(Y!==0||b.isRenderTargetTexture||xe.has(b)){const yn=xe.get(b),Qt=xe.get(j);fe.bindFramebuffer(U.READ_FRAMEBUFFER,Pr),fe.bindFramebuffer(U.DRAW_FRAMEBUFFER,Lr);for(let Sn=0;Sn<Ye;Sn++)zt?U.framebufferTextureLayer(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,yn.__webglTexture,Y,lt+Sn):U.framebufferTexture2D(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,yn.__webglTexture,Y),bn?U.framebufferTextureLayer(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,Qt.__webglTexture,Be,bt+Sn):U.framebufferTexture2D(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,Qt.__webglTexture,Be),Y!==0?U.blitFramebuffer(gt,_t,We,it,yt,Ut,We,it,U.COLOR_BUFFER_BIT,U.NEAREST):bn?U.copyTexSubImage3D(Ot,Be,yt,Ut,bt+Sn,gt,_t,We,it):U.copyTexSubImage2D(Ot,Be,yt,Ut,gt,_t,We,it);fe.bindFramebuffer(U.READ_FRAMEBUFFER,null),fe.bindFramebuffer(U.DRAW_FRAMEBUFFER,null)}else bn?b.isDataTexture||b.isData3DTexture?U.texSubImage3D(Ot,Be,yt,Ut,bt,We,it,Ye,Ft,dt,Bt.data):j.isCompressedArrayTexture?U.compressedTexSubImage3D(Ot,Be,yt,Ut,bt,We,it,Ye,Ft,Bt.data):U.texSubImage3D(Ot,Be,yt,Ut,bt,We,it,Ye,Ft,dt,Bt):b.isDataTexture?U.texSubImage2D(U.TEXTURE_2D,Be,yt,Ut,We,it,Ft,dt,Bt.data):b.isCompressedTexture?U.compressedTexSubImage2D(U.TEXTURE_2D,Be,yt,Ut,Bt.width,Bt.height,Ft,Bt.data):U.texSubImage2D(U.TEXTURE_2D,Be,yt,Ut,We,it,Ft,dt,Bt);U.pixelStorei(U.UNPACK_ROW_LENGTH,At),U.pixelStorei(U.UNPACK_IMAGE_HEIGHT,rn),U.pixelStorei(U.UNPACK_SKIP_PIXELS,si),U.pixelStorei(U.UNPACK_SKIP_ROWS,Cn),U.pixelStorei(U.UNPACK_SKIP_IMAGES,Dr),Be===0&&j.generateMipmaps&&U.generateMipmap(Ot),fe.unbindTexture()},this.initRenderTarget=function(b){xe.get(b).__webglFramebuffer===void 0&&Re.setupRenderTarget(b)},this.initTexture=function(b){b.isCubeTexture?Re.setTextureCube(b,0):b.isData3DTexture?Re.setTexture3D(b,0):b.isDataArrayTexture||b.isCompressedArrayTexture?Re.setTexture2DArray(b,0):Re.setTexture2D(b,0),fe.unbindTexture()},this.resetState=function(){H=0,I=0,N=null,fe.reset(),Ve.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return wi}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=Nt._getDrawingBufferColorSpace(e),t.unpackColorSpace=Nt._getUnpackColorSpace()}}const Uw=[-1,0,0,1,0,0,0,-1,-2,-1,-2,-1,-2,0,0,-1,-1,-1,-3,-1,1,0,-3,-1,-2,-2,3,5,-11,-7,-12],M0=[["#ed9b35","#4b1914","#63360c"],["#3096b0","#153b60","#123d50"],["#b9b17b","#25483e","#384937"]];function E0(s,e,t){const r=new Ld,o=-s/2,l=-e/2;return r.moveTo(o+t,l),r.lineTo(o+s-t,l),r.quadraticCurveTo(o+s,l,o+s,l+t),r.lineTo(o+s,l+e-t),r.quadraticCurveTo(o+s,l+e,o+s-t,l+e),r.lineTo(o+t,l+e),r.quadraticCurveTo(o,l+e,o,l+e-t),r.lineTo(o,l+t),r.quadraticCurveTo(o,l,o+t,l),r}function Fw(s,e){const{mode:t,on:r,progress:o,cover:l}=e,u=480,f=560;s.clearRect(0,0,u,f),s.fillStyle=t==="theater"&&r?M0[l][2]:"#101d22",s.fillRect(0,0,u,f);const d=(p,v,g,_=34,S="#e7f5f3",M="left")=>{s.font=`${_>=42?600:400} ${_}px Barlow, sans-serif`,s.fillStyle=S,s.textAlign=M,s.fillText(p,v,g)};if(d(t==="bluetooth"?r?"BT ON":"BT OFF":"CE / DAP NEO",28,43,28,"#abc6c9"),d("▰",450,43,28,"#a5d7be","right"),t==="bluetooth")d("Bluetooth",240,143,44,"#eef8f5","center"),d(r?"ON":"OFF",240,278,112,r?"#91e4d3":"#84999d","center"),s.fillStyle="#314348",s.fillRect(65,343,350,8),s.fillStyle="#ecab61",s.fillRect(65,343,350*o,8),d(e.holding?"Holding Power…":r?"Ready to pair":"Module off",240,410,34,"#e1eae6","center"),d("Long press / Power",240,498,30,"#a9c3c6","center");else if(t==="eq"){d("Heavy Metal",28,108,42),d(r?"HD 600 / fitted":"Stock preset",28,152,32,"#9fc5c8"),s.lineWidth=1,s.strokeStyle="#456067";for(let p=210;p<=410;p+=50)s.beginPath(),s.moveTo(28,p),s.lineTo(452,p),s.stroke();s.beginPath(),s.lineWidth=5,s.strokeStyle="#8de5d1",Uw.forEach((p,v)=>{const g=28+v*424/30,_=310-p*o*8;v?s.lineTo(g,_):s.moveTo(g,_)}),s.stroke(),d("20 Hz",28,459,29,"#abc6c9"),d("20 kHz",452,459,29,"#abc6c9","right"),d("31 bands / ±12 dB",240,522,30,"#d4e4df","center")}else if(t==="theater"){const[p,v]=M0[l],g=s.createLinearGradient(100,85,380,345);g.addColorStop(0,p),g.addColorStop(1,v),s.fillStyle=g,s.fillRect(103,82,274,260),s.fillStyle="#f8dbad",s.beginPath(),s.arc(288,216,47,0,Math.PI*2),s.fill(),d(["Evening light","Open water","Forest floor"][l],240,396,39,"#f5f1e5","center"),d("Sample artwork",240,439,30,"#cddbd1","center"),s.fillStyle="#ffffff44",s.fillRect(28,472,424,5),s.fillStyle="#fff",s.fillRect(28,472,154,5),d("01:24",28,526,28),d("04:13",452,526,28,"#d3dfd9","right")}else if(t==="playlist")d("Evening.m3u",28,119,43),["Evening light","Open water","Last train"].forEach((p,v)=>{v===(r?1:0)&&(s.fillStyle="#306969",s.fillRect(18,155+v*92,444,80)),d(`${String(v+1).padStart(2,"0")} / ${p}`,30,206+v*92,34)}),d("3 tracks / playlist",28,510,31,"#abc6c9");else if(t==="lockscreen")d("HOLD ENABLED",240,130,31,"#abc6c9","center"),d(r?"Evening light":"Playback",240,239,43,"#eef8f5","center"),d(r?"01:24":"—:—",240,350,84,"#91e4d3","center"),d("Track time",240,430,32,"#abc6c9","center");else if(t==="gapless"){d(r?"Track 02.flac":"Track 01.flac",240,150,40,"#eef8f5","center");for(let p=0;p<27;p++){s.fillStyle="#8de5d1";const v=24+p*31%116;s.fillRect(30+p*16,290-v/2,9,v)}d("Same-format playback",240,435,32,"#abc6c9","center")}else t==="opus"?(d("Opus playback",240,170,45,"#eef8f5","center"),d(".opus",240,310,92,"#91e4d3","center"),d("Standard image",240,440,34,"#abc6c9","center")):(d("Wheel timer",240,170,43,"#eef8f5","center"),d(r?"1,000":"2,500",240,310,88,"#91e4d3","center"),d("wakeups / second",240,430,33,"#abc6c9","center"))}function Ow({state:s,onHoldStart:e,onHoldEnd:t}){const r=Oe.useRef(null),o=Oe.useRef(s);o.current=s;const l=Oe.useRef({onHoldStart:e,onHoldEnd:t});l.current={onHoldStart:e,onHoldEnd:t};const u=Oe.useRef(()=>{});return Oe.useEffect(()=>{const f=r.current;if(!f)return;let d;try{d=new Iw({alpha:!0,antialias:!0,preserveDrawingBuffer:!0})}catch{f.dataset.unavailable="true";return}d.setPixelRatio(Math.min(window.devicePixelRatio,2)),d.outputColorSpace=Vn;const p=new oy,v=new ri(32,1,.1,30),g=["eq","lockscreen"].includes(o.current.mode),_=g?4.8:o.current.mode==="theater"?5.8:6.8,S=g?.6:.05;v.position.set(0,S,_),v.lookAt(0,S,0),p.add(new qy(15857663,5398636,3));const M=new Ym(16777215,4);M.position.set(-3,5,6),p.add(M);const A=new Ym(13100543,2);A.position.set(4,0,-2),p.add(A);const y=new jo;p.add(y),y.rotation.set(.06,-.32,-.1);const x=new Ul({color:12897747,metalness:.7,roughness:.34}),O=new Ul({color:1317664,metalness:.35,roughness:.45}),D=new an(new Dd(E0(1.82,3.4,.22),{depth:.15,bevelEnabled:!0,bevelSegments:4,steps:1,bevelSize:.045,bevelThickness:.045}),x);D.position.z=-.12,y.add(D);const R=new an(new Nd(E0(1.55,1.86,.17)),O);R.position.set(0,.65,.084),y.add(R);const z=document.createElement("canvas");z.width=480,z.height=560;const H=z.getContext("2d"),I=new uy(z);I.colorSpace=Vn;const N=new an(new ua(1.32,1.54),new Jl({map:I}));N.position.set(0,.65,.088),y.add(N);const C=new an(new Ql(.61,.61,.025,80),O);C.rotation.x=Math.PI/2,C.position.set(0,-.96,.095),y.add(C);const T=new an(new Ql(.23,.23,.035,64),new Ul({color:3423814,roughness:.5,metalness:.4}));T.rotation.x=Math.PI/2,T.position.set(0,-.96,.12),y.add(T);const F=new Ul({color:15571764,roughness:.3,metalness:.3,emissive:15571764,emissiveIntensity:0}),$=new an(new ji(.085,.23,.1),F);$.position.set(-.963,1.12,-.015),y.add($);for(const B of[.58,.08]){const Z=new an(new ji(.06,.31,.09),O);Z.position.set(-.95,B,-.015),y.add(Z)}const ee=new an(new ji(.3,.035,.065),O);ee.position.set(0,-1.72,0),y.add(ee);const le=new an(new ji(.43,.49,.6),new Jl({visible:!1}));le.position.copy($.position),y.add(le),d.domElement.setAttribute("aria-hidden","true"),f.append(d.domElement);const ne=()=>{Fw(H,o.current),I.needsUpdate=!0,F.emissiveIntensity=o.current.holding?.7:0,d.render(p,v)};u.current=ne;const ce=()=>{const{width:B,height:Z}=f.getBoundingClientRect();d.setSize(B,Z,!1),v.aspect=B/Z,v.updateProjectionMatrix(),ne()},re=new ResizeObserver(ce);re.observe(f),ce();let V=!1;const me=B=>{if(!l.current.onHoldStart)return;const Z=f.getBoundingClientRect(),ue=new Zy;ue.setFromCamera(new Ge((B.clientX-Z.left)/Z.width*2-1,-(B.clientY-Z.top)/Z.height*2+1),v),ue.intersectObject(le).length&&(V=!0,d.domElement.setPointerCapture(B.pointerId),l.current.onHoldStart(),B.preventDefault())},ie=()=>{V&&(V=!1,l.current.onHoldEnd?.())};d.domElement.addEventListener("pointerdown",me),d.domElement.addEventListener("pointerup",ie),d.domElement.addEventListener("pointercancel",ie),d.domElement.addEventListener("lostpointercapture",ie);let P=!0;return document.fonts.ready.then(()=>{P&&ne()}),()=>{P=!1,re.disconnect(),u.current=()=>{},d.domElement.removeEventListener("pointerdown",me),d.domElement.removeEventListener("pointerup",ie),d.domElement.removeEventListener("pointercancel",ie),d.domElement.removeEventListener("lostpointercapture",ie),p.traverse(B=>{B instanceof an&&(B.geometry.dispose(),(Array.isArray(B.material)?B.material:[B.material]).forEach(ue=>ue.dispose()))}),I.dispose(),d.dispose(),d.domElement.remove()}},[]),Oe.useEffect(()=>{u.current()},[s]),W.jsx("div",{className:"player-model",ref:r,role:"img","aria-label":s.mode==="bluetooth"?`DAP Neo screen: Bluetooth ${s.on?"on":"off"}${s.holding?", Power button held":""}`:s.mode==="eq"?`DAP Neo screen: ${s.on?"fitted HD 600 EQ curve":"stock EQ preset"}`:`DAP Neo ${s.mode} illustration`,children:W.jsx("span",{className:"player-model-fallback",children:"3D preview unavailable. Use the controls below to preview the feature."})})}const kw={on:!1,holding:!1,progress:0,cover:0},Bw={on:!0,holding:!1,progress:1,cover:1},zw=Object.fromEntries(["theater","eq","bluetooth","playlist","lockscreen","gapless","opus","system"].map(s=>[s,async e=>{if(await e.wait(900),e.mark("action"),s==="bluetooth"){await e.set({holding:!0});for(let t=1;t<=24;t++)await e.wait(50),e.put({progress:t/24});e.mark("paired"),await e.set({on:!0,holding:!1})}else{await e.set({on:!0,cover:1});for(let t=1;t<=20;t++)await e.wait(45),e.put({progress:t/20});e.mark("result")}await e.wait(2200)}]));function Hw({mode:s,scene:e}){const[t,r]=Oe.useState(null),o=t??{...e,mode:s},l=Oe.useRef(o);l.current=o;const u=Oe.useRef(0),f=Oe.useRef(!1),d=()=>{f.current&&(f.current=!1,cancelAnimationFrame(u.current),r(g=>g&&{...g,holding:!1,progress:0}))},p=()=>{if(f.current)return;f.current=!0;const g=l.current,_=performance.now(),S=()=>{const M=Math.min(1,(performance.now()-_)/1200);r({...g,holding:M<1,progress:M,on:M===1?!g.on:g.on}),M<1?u.current=requestAnimationFrame(S):f.current=!1};S()};Oe.useEffect(()=>{const g=()=>{cancelAnimationFrame(u.current),f.current=!1,r(_=>_&&{..._,holding:!1,progress:0})};return window.addEventListener("blur",g),()=>{cancelAnimationFrame(u.current),window.removeEventListener("blur",g)}},[]);const v=g=>{if(cancelAnimationFrame(u.current),s!=="eq"){r({...l.current,...g});return}const _=l.current,S=g.on?1:0,M=performance.now(),A=()=>{const y=Math.min(1,(performance.now()-M)/650),x=1-Math.pow(1-y,3);r({..._,...g,progress:_.progress+(S-_.progress)*x}),y<1&&(u.current=requestAnimationFrame(A))};A()};return W.jsxs("div",{className:"device-demo","data-mode":s,"data-on":o.on,"data-holding":o.holding,children:[W.jsx(Ow,{state:o,onHoldStart:s==="bluetooth"?p:void 0,onHoldEnd:d}),s==="bluetooth"&&W.jsxs("div",{className:"demo-controls",children:[W.jsx(hl,{size:"large",className:"demo-hold",tabIndex:0,"aria-label":"Hold Power for 1.2 seconds to toggle Bluetooth preview","data-target":"power-preview","aria-pressed":o.on,onPointerDown:g=>{g.currentTarget.setPointerCapture(g.pointerId),p()},onPointerUp:d,onPointerCancel:d,onLostPointerCapture:d,onKeyDown:g=>{(g.key===" "||g.key==="Enter")&&(g.preventDefault(),g.repeat||p())},onKeyUp:g=>{(g.key===" "||g.key==="Enter")&&(g.preventDefault(),d())},onBlur:d,children:"Hold Power"}),W.jsx("span",{className:"demo-instruction",children:"Hold the orange side button or this control for 1.2 seconds."})]}),s==="eq"&&W.jsxs("div",{className:"demo-controls",children:[W.jsxs("div",{className:"demo-options",role:"group","aria-label":"EQ curve preview",children:[W.jsx(hl,{size:"large",tabIndex:0,"aria-pressed":!o.on,onClick:()=>v({on:!1,progress:0}),onKeyDown:g=>{(g.key==="Enter"||g.key===" ")&&(g.preventDefault(),v({on:!1,progress:0}))},children:"Stock preset"}),W.jsx(hl,{size:"large",tabIndex:0,"aria-pressed":o.on,onClick:()=>v({on:!0,progress:1}),onKeyDown:g=>{(g.key==="Enter"||g.key===" ")&&(g.preventDefault(),v({on:!0,progress:1}))},children:"HD 600 curve"})]}),W.jsx("span",{className:"demo-instruction",children:"Compare the preset and fitted curve on the player’s screen."})]}),s==="theater"&&W.jsxs("div",{className:"demo-controls",children:[W.jsx("div",{className:"demo-options",role:"group","aria-label":"Sample artwork",children:["Evening light","Open water","Forest floor"].map((g,_)=>W.jsx(hl,{size:"large",tabIndex:0,"aria-pressed":o.cover===_,onClick:()=>v({cover:_,on:!0}),onKeyDown:S=>{(S.key==="Enter"||S.key===" ")&&(S.preventDefault(),v({cover:_,on:!0}))},children:g},g))}),W.jsx("span",{className:"demo-instruction",children:"Choose artwork to change the playback background."})]})]})}function Vw({theme:s,width:e,mode:t}){const r=["eq","bluetooth","theater"].includes(t);return W.jsx(tc,{width:e,height:r?540:430,initial:kw,poster:Bw,script:zw[t],play:"once",theme:s,accent:"var(--ce-accent)",tokens:{"--ss-font":"var(--ce-font)"},unframed:!0,className:"ft-stage device-stage",children:o=>W.jsx(Hw,{mode:t,scene:o})})}async function Gw(s){await s.wait(900),s.mark("change"),await s.set({on:!0}),await s.wait(2400)}function Ww({theme:s,width:e,mode:t}){return W.jsx(tc,{width:e,height:280,initial:{on:!1},poster:{on:!0},play:"once",script:Gw,theme:s,accent:"var(--ce-accent)",tokens:{"--ss-font":"var(--ce-font)"},className:"ft-stage detail-stage",children:r=>W.jsx("div",{className:"detail-scene","data-detail":t,"data-on":r.on,children:t==="playlist"?W.jsxs(N0,{pad:"large",gap:16,className:"detail-playlist",children:[W.jsxs("div",{className:"detail-list-title",children:["Evening.m3u ",W.jsx("span",{children:"3 tracks"})]}),W.jsxs("div",{className:"detail-tracks",children:[W.jsx("div",{className:"detail-track-highlight",style:{transform:`translateY(${r.on?44:0}px)`}}),["Evening light","Open water","Last train"].map((o,l)=>W.jsxs("div",{className:"detail-track",children:[W.jsxs("span",{children:["0",l+1]}),W.jsx("span",{children:o}),W.jsx("span",{children:["04:13","03:28","05:02"][l]})]},o))]}),W.jsx("div",{className:"detail-list-foot",children:"Next and shuffle stay in this playlist."})]}):t==="opus"?W.jsxs("div",{className:"detail-formats",children:[W.jsxs("div",{className:"detail-format",children:[W.jsx("span",{children:"Minimal"}),W.jsx("strong",{children:".wma"}),W.jsx("small",{children:"WMA retained"})]}),W.jsxs("div",{className:"detail-format detail-format--active",children:[W.jsx("span",{children:"Standard"}),W.jsx("strong",{children:".opus"}),W.jsx("small",{children:"Opus replaces WMA"})]})]}):t==="system"?W.jsxs("div",{className:"detail-timer",children:[W.jsxs("div",{className:"detail-bar-label",children:[W.jsx("span",{children:"Stock wheel timer"}),W.jsx("strong",{children:"2,500 / s"})]}),W.jsx("div",{className:"detail-bar",children:W.jsx("i",{})}),W.jsxs("div",{className:"detail-bar-label",children:[W.jsx("span",{children:"CE wheel timer"}),W.jsx("strong",{children:"1,000 / s"})]}),W.jsx("div",{className:"detail-bar detail-bar--ce",children:W.jsx("i",{style:{width:r.on?"40%":"100%"}})}),W.jsxs("p",{children:["60% fewer timer wakeups.",W.jsx("br",{}),"Battery-life gains have not been measured."]})]}):W.jsxs("div",{className:"detail-gapless",children:[W.jsxs("div",{className:"detail-wave-label",children:[W.jsx("span",{children:"Track 01.flac"}),W.jsx("span",{children:"Track 02.flac"})]}),W.jsxs("svg",{viewBox:"0 0 440 90",role:"img","aria-label":"Two same-format tracks joining without a decoder reload",children:[Array.from({length:44},(o,l)=>W.jsx("rect",{x:l*10+2,y:45-(14+l*23%60)/2,width:"5",height:14+l*23%60,rx:"2",className:l<22?"wave-first":"wave-second"},l)),W.jsx("rect",{className:"detail-gap",x:"212",y:"0",width:r.on?"0":"16",height:"90"})]}),W.jsxs("div",{className:"detail-join",children:[W.jsx("i",{}),W.jsx("span",{children:"Track boundary"})]}),W.jsx(X_,{value:r.on?"ce":"stock",states:{stock:"Stock: reload, reset, ready poll",ce:"CE: same-format decoder fast path"}})]})})})}const xg=110,yg=450,Xw={on:!1},jw={on:!0},qw=s=>async e=>{await e.wait(yg+s*xg),await e.set({on:!0})};function Yw(){const s=ro(),e=Oe.useRef(null),[t,r]=Oe.useState(!1);return Oe.useLayoutEffect(()=>{const o=e.current;if(!o)return;let l=0;const u=new IntersectionObserver(([f])=>{f.isIntersecting&&(u.disconnect(),l=window.setTimeout(()=>r(!0),yg+xg))},{threshold:.4});return u.observe(o),()=>{u.disconnect(),clearTimeout(l)}},[]),W.jsxs("span",{ref:e,className:"ft-stat-number",children:[W.jsx(V_,{value:t||s?40:0,duration:1100}),W.jsx("span",{className:"ft-stat-unit",children:" dB"})]})}const $w=["Track 1","Track 2","Track 10"];function Kw({theme:s,width:e}){const t=Math.max(200,e-48);return W.jsx(tc,{width:e,height:224,initial:Xw,poster:jw,play:"once",script:qw(3),theme:s,accent:"var(--ce-accent)",className:"ft-stage",children:r=>{const o=r.on?[0,1,2]:[0,2,1];return W.jsx(N0,{pad:"small",lift:!0,className:"ft-sort",style:{width:t},children:W.jsxs("div",{className:"ft-sort-rows",children:[$w.map((l,u)=>W.jsxs("div",{className:"ft-sort-row","data-moving":u===2||void 0,style:{transform:`translateY(${o[u]*40}px)`},children:[W.jsx("span",{className:"ft-sort-no",children:o[u]+1}),W.jsx("span",{className:"ft-sort-name",children:l}),W.jsx(Bu,{w:[44,38,50][u],h:6,tone:2})]},l)),[0,1,2].map(l=>W.jsxs("div",{className:"ft-sort-row",style:{transform:`translateY(${(3+l)*40}px)`},children:[W.jsx("span",{className:"ft-sort-no",children:4+l}),W.jsx(Bu,{w:[72,60,80][l],h:7,tone:3}),W.jsx(Bu,{w:[40,46,36][l],h:6,tone:2})]},l))]})})}})}const Bl=s=>e=>W.jsx(Vw,{...e,mode:s}),zl=s=>e=>W.jsx(Ww,{...e,mode:s}),Zw={theater:Bl("theater"),eq:Bl("eq"),sort:Kw,bluetooth:Bl("bluetooth"),playlist:zl("playlist"),lockscreen:Bl("lockscreen"),gapless:zl("gapless"),opus:zl("opus"),system:zl("system")};function Jw({node:s,theme:e}){const[t,r]=Oe.useState(()=>Math.max(1,Math.round(s.getBoundingClientRect().width))||340);Oe.useLayoutEffect(()=>{const l=()=>r(Math.max(1,Math.round(s.getBoundingClientRect().width)));l();const u=new ResizeObserver(l);return u.observe(s),()=>u.disconnect()},[s]);const o=Zw[s.dataset.picture];return o?Yl.createPortal(W.jsx(o,{theme:e,width:t}),s):null}function Qw({theme:s,root:e}){const t=[...e.querySelectorAll("[data-picture]")],r=e.querySelector('[data-stat="vorbis"]');return W.jsxs(W.Fragment,{children:[t.map(o=>W.jsx(Jw,{node:o,theme:s},o.dataset.picture)),r&&Yl.createPortal(W.jsx(Yw,{}),r)]})}const md=window.matchMedia("(prefers-color-scheme: dark)"),w0=()=>md.matches?"dark":"light";function Sg(){const[s,e]=Oe.useState(w0);return Oe.useEffect(()=>{const t=()=>e(w0());return md.addEventListener("change",t),()=>md.removeEventListener("change",t)},[]),s}function e2(){return W.jsx(k_,{theme:Sg()})}function t2({root:s}){return W.jsx(Qw,{theme:Sg(),root:s})}const T0=document.getElementById("ce-hero-stage");T0&&R0.createRoot(T0).render(W.jsx(Oe.StrictMode,{children:W.jsx(e2,{})}));const Hl=document.getElementById("features");if(Hl){Hl.querySelector("[data-stat]")?.replaceChildren();const s=document.createElement("div");s.hidden=!0,Hl.append(s),R0.createRoot(s).render(W.jsx(Oe.StrictMode,{children:W.jsx(t2,{root:Hl})}))}
