#!/usr/bin/env python3

# Created by Rahul Suthar# Creation Date: 12-Jun-2025
# DESCRIPTION:
#
# Script Name: Depth Sensing Backdrill Coupon
# Version: 1.0
#
from Environment import *
from GenesisJob import GenesisJob
from GenesisMatrix import GenesisMatrix
from GenesisStep import GenesisStep
from GenesisLayer import GenesisLayer
from GenesisAnalysisReport import GenesisAnalysisReport
import DialogBox
from css import CURRENT_STYLE
from CustomWidgets import MessageOk, MessageOkCancel

import os
import sys
import time
import json
import pathlib
from PyQt5 import QtWidgets, QtGui, QtCore


class DepthSensingBackdrillCoupon:
    def __init__(self, job_name, config_path=None):
        """Initialize the Depth Sensing Backdrill Coupon class."""

        self.site = SITE_NAME
        self.job_name = job_name
        self.GENJOB = GenesisJob(job_name)
        self.GENMAT = GenesisMatrix(job_name)
        self.GENSTEP = GenesisStep(job_name, EDITS_STEP_NAME)
        
        
        self.config = {}

        # Load configuration
        if config_path is None:
            # Use default config path
            self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'DepthSensing_config.json')
        else:
            self.config_path = config_path
        
        # Try to load the default config first
        self.config = self.load_config(config_path=self.config_path)

        # Then try to load the site-specific config and update the default config
        site_config = self.load_config(config_path=os.path.join(os.path.dirname(__file__), 'config', f'{self.site}_DepthSensing_config.json'))

        if site_config:  # Only update if the site config was successfully loaded
            self.config.update(site_config)

        self.GENSTEP_CPN = GenesisStep(job_name, self.config["coupon_name"])
        

        # For debugging
        print('==='*35)
        print(f"Configuration Loaded: {self.config}")
        print(f"Job: {self.job_name}, Site: {self.site}, Coupon Step Name: {self.config["coupon_name"]}")
        print('==='*35)

        
    def load_config(self,config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}")
            MessageOk(title="Configuration Error", text=f"Config file not found at {config_path}. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print(f"Error parsing config file {config_path}")
            MessageOk(title="Configuration Error", text=f"Error parsing config file {config_path}. Using default settings.")
            return {}

            
    def setup_application(self):
        """Set up PyQt application for GUI if not already done."""
        if QtWidgets.QApplication.instance() is None:
            self.app = QtWidgets.QApplication(sys.argv)
        else:
            self.app = QtWidgets.QApplication.instance()
    
    def add_clamping_hole_features(self):
        if self.GENJOB.stepExists(self.config["coupon_name"]):
            self.GENJOB.deleteStep(self.config["coupon_name"])

        # Create the coupon step
        self.GENJOB.createStep(self.config["coupon_name"])
        
        self.GENSTEP_CPN.openEditor(clear=True,zoom_home=True)
        # Create pth_hole_lay_name layer if it doesn't exist
        if not self.GENJOB.layerExists(self.config["pth_hole_lay_name"]):
            self.GENSTEP_CPN.createLayer(layer_name = self.config["pth_hole_lay_name"], layer_type="drill", context="board", polarity="positive")

        # Create drill_sense_lay_name layer if it doesn't exist
        if not self.GENJOB.layerExists(self.config["drill_sense_lay_name"]):
            self.GENSTEP_CPN.createLayer(layer_name = self.config["drill_sense_lay_name"], layer_type="drill", context="board", polarity="positive")

        self.GENSTEP_CPN.workOnFirstLayer(layer_name=self.config["pth_hole_lay_name"],clear_layers=True)
        self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={self.config["pth_hole_x_location"]},y={self.config["pth_hole_y_location"]},symbol=r{self.config["pth_hole_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

        Work_Layers = self.GENMAT.cuLayersNames() + [TOP_MASK_NAME, BOT_MASK_NAME]
        for layer in Work_Layers:
            # if not layer: continue
            if not self.GENJOB.layerExists(layer) or not layer: continue
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=layer,clear_layers=True)
            self.WIP_LAY = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=layer)
            # if self.WIP_LAY.getPolarity() == "positive":
            #     self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={self.config["pth_hole_x_location"]},y={self.config["pth_hole_y_location"]},symbol=r{self.config["pth_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            # else:
            #     self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={self.config["pth_hole_x_location"]},y={self.config["pth_hole_y_location"]},symbol=r{self.config["pth_hole_pad_size"]},polarity=negative,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={self.config["pth_hole_x_location"]},y={self.config["pth_hole_y_location"]},symbol=r{self.config["pth_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

    # def get_backdrill_info(self):
    #     """Retrieve backdrill information from the Genesis job."""
    #     backdrill_layers = []
    #     for layer in self.GENMAT.drillLayersNames():
    #         # if not layer: continue
    #         if not self.GENJOB.layerExists(layer) or not layer: continue
    #         if not layer.startswith(self.config["backdrill_lay_name"]): continue
    #         backdrill_layers.append(layer)

    #     print(f"Backdrill Layers: {backdrill_layers}")
    #     return backdrill_layers
    
    def get_drill_span(self):
        drill_span_list = []
        for row in self.GENMAT.ROWS:
            drill_span = {}
            if not row['name'].startswith(self.config["backdrill_lay_name"]): continue

            if row['drl_start'] != '' and row['drl_end'] != '':
                drill_span['name'] = row['name']
                if row['drl_start'] in self.GENMAT.cuLayersNames():
                    drill_span['drl_start'] = row['drl_start']
                elif row['drl_start'] in [TOP_MASK_NAME, TOP_PASTE_NAME, TOP_SILK_NAME]:
                    drill_span['drl_start'] = TOP_LAYER_NAME
                elif row['drl_start'] in [BOT_MASK_NAME, BOT_PASTE_NAME, BOT_SILK_NAME]:
                    drill_span['drl_start'] = BOT_LAYER_NAME


                if row['drl_end'] in self.GENMAT.cuLayersNames():
                    drill_span['drl_end'] = row['drl_end']
                elif row['drl_end'] in [TOP_MASK_NAME, TOP_PASTE_NAME, TOP_SILK_NAME]:
                    drill_span['drl_end'] = TOP_LAYER_NAME
                elif row['drl_end'] in [BOT_MASK_NAME, BOT_PASTE_NAME, BOT_SILK_NAME]:
                    drill_span['drl_end'] = BOT_LAYER_NAME

                drill_span_list.append(drill_span)
        
        print(f"Drill Span List: {drill_span_list}")
        # Example Ouput: Drill Span List: [{'name': 'bd1.4-3', 'drl_start': 'pgp3', 'drl_end': 'bot'}]
        return drill_span_list
    
    # def add_drill_sense_features(self):
    #     """Add drill sense features to the coupon step."""
        
    #     count = 2
    #     # x_position_increment = 0
    #     # y_position_offset = 0.05

    #     X_Pos = self.config["pth_hole_x_location"] + self.config["drill_sense_x_location_offset"]
    #     Y_Pos = self.config["pth_hole_y_location"] + self.config["drill_sense_y_location_offset"]

    #     for drill_lay in self.get_drill_span():

    #         # print(f"Processing Backdrill Layer: {drill_lay['name']}")
    #         self.GENSTEP_CPN.workOnFirstLayer(layer_name=self.config["drill_sense_lay_name"],clear_layers=True)
    #         self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

    #         # print(f"Processing Span Start Layer: {drill_lay['drl_start']}")
    #         self.GENSTEP_CPN.workOnFirstLayer(layer_name=drill_lay['drl_start'],clear_layers=True)
    #         self.WIP_LAY_start = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=drill_lay['drl_start'])
    #         self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity={self.WIP_LAY_start.getPolarity()},angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
    #         # Add Line on Start layer
    #         if drill_lay['drl_start'] != self.GENMAT.topOuterLayerName() and drill_lay['drl_start'] != self.GENMAT.bottomOuterLayerName():
    #             self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={Y_Pos},xe={X_Pos},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity={self.WIP_LAY_start.getPolarity()},bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
    #             self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={self.config["pth_hole_y_location"]},xe={self.config["pth_hole_x_location"]},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity={self.WIP_LAY_start.getPolarity()},bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
    #         else:
    #             self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={X_Pos-self.config["text_x"]/3},y={self.config["drill_sense_y_location_offset"]/2},text={count},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')

    #         # print(f"Processing Span End Layer: {drill_lay['drl_end']}")
    #         self.GENSTEP_CPN.workOnFirstLayer(layer_name=drill_lay['drl_end'],clear_layers=True)
    #         self.WIP_LAY_end = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=drill_lay['drl_end'])
    #         self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity={self.WIP_LAY_end.getPolarity()},angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
    #         # Add Line on End layer
    #         if drill_lay['drl_end'] != self.GENMAT.topOuterLayerName() and drill_lay['drl_end'] != self.GENMAT.bottomOuterLayerName():
    #             self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={Y_Pos},xe={X_Pos},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity={self.WIP_LAY_end.getPolarity()},bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
    #             self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={self.config["pth_hole_y_location"]},xe={self.config["pth_hole_x_location"]},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity={self.WIP_LAY_end.getPolarity()},bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
    #         else:
    #             self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={X_Pos-self.config["text_x"]/3},y={self.config["drill_sense_y_location_offset"]/2},text={count},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')


    #         for MASK_LAY in [TOP_MASK_NAME, BOT_MASK_NAME]:
    #             # print(f"Processing {MASK_LAY} Layer")
    #             if not self.GENJOB.layerExists(MASK_LAY): continue
    #             if MASK_LAY == TOP_MASK_NAME and drill_lay['drl_start'] is not TOP_LAYER_NAME: continue
    #             if MASK_LAY == BOT_MASK_NAME and drill_lay['drl_end'] is not BOT_LAYER_NAME: continue
    #             self.GENSTEP_CPN.workOnFirstLayer(layer_name=MASK_LAY,clear_layers=True)
    #             self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]+5},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

    #         count += 1
    #         X_Pos += self.config["drill_sense_x_location_offset"]
        
    #     self.add_top_bot_text()

    #     self.add_profile_to_cpn()

    #     self.add_thieving()

    #     if self.GENSTEP_CPN.layerExists(TOP_LAYER_NAME):
    #         self.GENSTEP_CPN.workOnFirstLayer(layer_name=TOP_LAYER_NAME,clear_layers=True)

    def add_drill_sense_features(self):
        count = 1
        X_Pos = self.config["pth_hole_x_location"] + self.config["drill_sense_x_location_offset"]
        Y_Pos = self.config["pth_hole_y_location"] + self.config["drill_sense_y_location_offset"]
        for drill_lay in self.get_drill_span():
            # print(f"Processing Backdrill Layer: {drill_lay['name']}")
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=self.config["drill_sense_lay_name"],clear_layers=True)
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            # print(f"Processing Span Start Layer: {drill_lay['drl_start']}")
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=drill_lay['drl_start'],clear_layers=True)
            self.WIP_LAY_start = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=drill_lay['drl_start'])
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            # Add Line on Start layer
            if drill_lay['drl_start'] != self.GENMAT.topOuterLayerName() and drill_lay['drl_start'] != self.GENMAT.bottomOuterLayerName():
                self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={Y_Pos},xe={X_Pos},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
                self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={self.config["pth_hole_y_location"]},xe={self.config["pth_hole_x_location"]},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
            else:
                self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={X_Pos-self.config["text_x"]/3},y={self.config["drill_sense_y_location_offset"]/2},text={count},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')
            # print(f"Processing Span End Layer: {drill_lay['drl_end']}")
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=drill_lay['drl_end'],clear_layers=True)
            self.WIP_LAY_end = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=drill_lay['drl_end'])
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            # Add Line on End layer
            if drill_lay['drl_end'] != self.GENMAT.topOuterLayerName() and drill_lay['drl_end'] != self.GENMAT.bottomOuterLayerName():
                self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={Y_Pos},xe={X_Pos},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
                self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={self.config["pth_hole_y_location"]},xe={self.config["pth_hole_x_location"]},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
            else:
                self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={X_Pos-self.config["text_x"]/3},y={self.config["drill_sense_y_location_offset"]/2},text={count},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')

            for MASK_LAY in [TOP_MASK_NAME, BOT_MASK_NAME]:
                # print(f"Processing {MASK_LAY} Layer")
                if not self.GENJOB.layerExists(MASK_LAY): continue
                if MASK_LAY == TOP_MASK_NAME and drill_lay['drl_start'] is not TOP_LAYER_NAME: continue
                if MASK_LAY == BOT_MASK_NAME and drill_lay['drl_end'] is not BOT_LAYER_NAME: continue
                self.GENSTEP_CPN.workOnFirstLayer(layer_name=MASK_LAY,clear_layers=True)
                self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]+5},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

            count += 1
            X_Pos += self.config["drill_sense_x_location_offset"]
        
        self.add_top_bot_text()

        self.add_profile_to_cpn()

        self.add_thieving()

        if self.GENSTEP_CPN.layerExists(TOP_LAYER_NAME):
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=TOP_LAYER_NAME,clear_layers=True)
        
    def add_top_bot_text(self):
        
        if self.GENSTEP_CPN.layerExists(TOP_LAYER_NAME):
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=TOP_LAYER_NAME,clear_layers=True)
            self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x=0.0061,y=0.101,text=TOP,x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')

        if self.GENSTEP_CPN.layerExists(BOT_LAYER_NAME):
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=BOT_LAYER_NAME,clear_layers=True)
            self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x=0.118,y=0.101,text=BOT,x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=yes,fontname={self.config["font_type"]},ver=1')

    def add_profile_to_cpn(self):
        CPN_Limits = self.GENSTEP_CPN.LIMITS()
        self.GENSTEP_CPN.COM(f'profile_rect,x1=0,y1=0,x2={CPN_Limits["xmax"]+0.025},y2={CPN_Limits["ymax"]+0.010}')

    def add_thieving(self):
        """Add thieving features to the coupon step."""
        # First create Blank layer to fill
        if self.GENJOB.layerExists("thiev_tmp+++"):
            self.GENSTEP_CPN.deleteLayer("thiev_tmp+++")

        self.GENSTEP_CPN.createLayer(layer_name = "thiev_tmp+++", polarity="positive")
        self.GENSTEP_CPN.workOnFirstLayer(layer_name="thiev_tmp+++",clear_layers=True)
        
        for layer in self.GENMAT.cuLayersNames():
            if not self.GENJOB.layerExists(layer) or not layer: continue
            if layer in [TOP_LAYER_NAME, BOT_LAYER_NAME]: continue
            self.WIP_LAY = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=layer)
            # Fill That layer
            self.GENSTEP_CPN.COM(f'sr_fill,polarity=positive,step_margin_x=0.0035,step_margin_y=0.0035,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no')
            # Clip that with required layers
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=15,ref_layer=epoxy,feat_types=line\;pad\;surface\;arc\;text')
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=15,ref_layer=drill_sense,feat_types=line\;pad\;surface\;arc\;text')
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=7,ref_layer={layer},feat_types=line\;pad\;surface\;arc\;text')
            # Move the thieving to actual layer
            self.GENSTEP_CPN.COM(f'sel_move_other,target_layer={layer},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')

            if self.WIP_LAY.getPolarity() == "negative":
                self.GENSTEP_CPN.COM(f'sr_fill,polarity=positive,step_margin_x=0.0035,step_margin_y=0.0035,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no')
                self.GENSTEP_CPN.workOnFirstLayer(layer_name=layer,clear_layers=True)
                self.GENSTEP_CPN.COM(f'sel_move_other,target_layer=thiev_tmp+++,invert=yes,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
                self.GENSTEP_CPN.workOnFirstLayer(layer_name="thiev_tmp+++",clear_layers=True)
                self.GENSTEP_CPN.COM(f'profile_to_rout,layer=thiev_tmp+++,width=7')
                self.GENSTEP_CPN.COM(f'sel_move_other,target_layer={layer},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')

        # Delete existing thieving layer if exists
        self.GENSTEP_CPN.deleteLayer("thiev_tmp+++")

if __name__ == '__main__':
    print("This script is started Running!")

    # Example usage: create an instance of the class and call setup_application
    dsbc = DepthSensingBackdrillCoupon(job_name=JOB)

    dsbc.add_clamping_hole_features()

    dsbc.add_drill_sense_features()
