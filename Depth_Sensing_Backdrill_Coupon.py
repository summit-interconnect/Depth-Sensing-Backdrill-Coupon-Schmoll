#!/usr/bin/env python3

# Created by Rahul Suthar# Creation Date: 12-Jun-2025
# DESCRIPTION:
#
# Script Name: Depth Sensing Backdrill Coupon
# Version: 1.0

import os
import json
from Environment import *
from GenesisJob import GenesisJob
from GenesisMatrix import GenesisMatrix
from GenesisStep import GenesisStep
from GenesisLayer import GenesisLayer

class DepthSensingBackdrillCoupon:
    def __init__(self, job_name, config_path=None):
        self.site_name = SITE_NAME
        self.site = SITE
        self.job_name = job_name
        self.GENJOB = GenesisJob(job_name)
        self.GENMAT = GenesisMatrix(job_name)
        self.GENSTEP = GenesisStep(job_name, EDITS_STEP_NAME)
        self.config = {}
        # Load configuration
        if config_path is None:
            # Use default config path
            self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'DepthSensing.json')
        else:
            self.config_path = config_path
        
        # Try to load the default config first
        self.config = self.load_config(config_path=self.config_path)
        # Then try to load the site-specific config and update the default config
        site_config = self.load_config(config_path=os.path.join(os.path.dirname(__file__), 'config', f'{self.site}_DepthSensing.json'))
        if site_config:  # Only update if the site config was successfully loaded
            self.config.update(site_config)
        self.GENSTEP_CPN = GenesisStep(job_name, self.config["coupon_name"])

        # For debugging
        print('==='*35)
        print(f"Configuration Loaded: {self.config}")
        print(f"Job: {self.job_name}, Site: {self.site}, Coupon Step Name: {self.config['coupon_name']}")
        print('==='*35)
        
    def load_config(self,config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
            return {}
    
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
        # Add pad on all cu layers
        for layer in self.GENMAT.cuLayersNames():
            if not self.GENJOB.layerExists(layer) or not layer: continue
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=layer,clear_layers=True)
            self.WIP_LAY = GenesisLayer(job_name=JOB, step_name=self.config["coupon_name"], layer_name=layer)
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={self.config["pth_hole_x_location"]},y={self.config["pth_hole_y_location"]},symbol=r{self.config["pth_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')

    def get_cu_number_to_name_map_info(self, get_value: int):
        cu_number_to_name = {}
        for idx, layer_name in enumerate(self.GENMAT.cuLayersNames(), start=1):
            cu_number_to_name[(idx)] = layer_name
        
        if get_value and cu_number_to_name:
            cu_name = cu_number_to_name.get(get_value, None)
            return cu_name

        return None

    def get_backdrill_info(self):
        drill_span_list = []
        for row in self.GENMAT.ROWS:
            drill_span = {}
            if not row['name'].startswith(BACKDRILL_PREFIX): continue
            if not row['drl_start'] != '' and not row['drl_end'] != '': continue
            drill_span['name'] = row['name']
            if SITE_NAME == "ANAHEIM":
                # Extract start_cu_num and end_cu_num from drill_span['name'], e.g. 'bd1.4-3'
                name_parts = drill_span['name'][2:].split('-')
                start_cu_num = int(name_parts[0].split('.')[1])
                end_cu_num = int(name_parts[1])

            if SITE_NAME == "ORANGE" or SITE_NAME == "HOLLISTER":
                # Extract start_cu_num and end_cu_num from drill_span['name'], e.g. 'bdrill_1-2'
                name_parts = drill_span['name'][2:].split('-')
                start_cu_num = int(name_parts[0].split('_')[1])
                end_cu_num = int(name_parts[1])

            if SITE_NAME == "CHICAGO":
                pass

            drill_span['start_cu_num'] = start_cu_num
            drill_span['end_cu_num'] = end_cu_num
            drill_span['start_cu_name'] = self.get_cu_number_to_name_map_info(get_value=start_cu_num)
            drill_span['end_cu_name'] = self.get_cu_number_to_name_map_info(get_value=end_cu_num)
            drill_span['drl_start'] = drill_span['start_cu_name']
            if start_cu_num < end_cu_num:
                drill_span['drl_mnc'] = self.get_cu_number_to_name_map_info(get_value=end_cu_num + 1)
            else:
                drill_span['drl_mnc'] = self.get_cu_number_to_name_map_info(get_value=end_cu_num - 1)

            drill_span_list.append(drill_span)
        
        print(f"Drill Span List: {drill_span_list}")
        # Example output --> Drill Span List: [{'name': 'bdrill_1-2', 'start_cu_num': 1, 'end_cu_num': 2, 'start_cu_name': 'top', 'end_cu_name': 'pgp2', 'drl_start': 'top', 'drl_mnc': 'pgp3'}, {'name': 'bdrill_4-3', 'start_cu_num': 4, 'end_cu_num': 3, 'start_cu_name': 'bot', 'end_cu_name': 'pgp3', 'drl_start': 'bot', 'drl_mnc': 'pgp2'}]
        return drill_span_list
        
    def add_top_bot_text(self, lay_name=TOP_LAYER_NAME, text="TOP", xPos=0.0061, yPos=0.101, mirror="no"):
        if self.GENSTEP_CPN.layerExists(lay_name):
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=lay_name,clear_layers=True)
            self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={xPos},y={yPos},text={text},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror={mirror},fontname={self.config["font_type"]},ver=1')
        
    def add_profile_to_cpn(self):
        CPN_Limits = self.GENSTEP_CPN.LIMITS()
        self.GENSTEP_CPN.COM(f'profile_rect,x1=0,y1=0,x2={CPN_Limits["xmax"]+0.025},y2={CPN_Limits["ymax"]+0.010}')

    def add_thieving(self):
        # Delete existing temp layer if exists
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
            # Clip that with required layer
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=15,ref_layer=epoxy,feat_types=line\;pad\;surface\;arc\;text')
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=15,ref_layer=drill_sense,feat_types=line\;pad\;surface\;arc\;text')
            self.GENSTEP_CPN.COM(f'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,contour_cut=yes,margin=7,ref_layer={layer},feat_types=line\;pad\;surface\;arc\;text')
            # Move the thieving to actual layer
            self.GENSTEP_CPN.COM(f'sel_move_other,target_layer={layer},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
            # Handle if Negative layer
            if self.WIP_LAY.getPolarity() == "negative":
                self.GENSTEP_CPN.COM(f'sr_fill,polarity=positive,step_margin_x=0.0035,step_margin_y=0.0035,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no')
                self.GENSTEP_CPN.workOnFirstLayer(layer_name=layer,clear_layers=True)
                self.GENSTEP_CPN.COM(f'sel_move_other,target_layer=thiev_tmp+++,invert=yes,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
                self.GENSTEP_CPN.workOnFirstLayer(layer_name="thiev_tmp+++",clear_layers=True)
                self.GENSTEP_CPN.COM(f'profile_to_rout,layer=thiev_tmp+++,width=7')
                self.GENSTEP_CPN.COM(f'sel_move_other,target_layer={layer},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
        # Delete existing temp layer if exists
        self.GENSTEP_CPN.deleteLayer("thiev_tmp+++")
    
    def add_mask_openings(self, cu_lay_name: str, mask_lay_name: str):
        if not self.GENJOB.layerExists(cu_lay_name) or not self.GENJOB.layerExists(mask_lay_name): return
        self.GENSTEP_CPN.workOnFirstLayer(layer_name=cu_lay_name,clear_layers=True)
        self.GENSTEP_CPN.COM('filter_reset,filter_name=popup')
        self.GENSTEP_CPN.COM(f'filter_set,filter_name=popup,update_popup=no,include_syms=r{self.config['pth_hole_pad_size']}\;r{self.config['drill_sense_hole_pad_size']}')
        self.GENSTEP_CPN.COM('filter_area_strt')
        self.GENSTEP_CPN.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no')
        self.GENSTEP_CPN.COM(f'sel_copy_other,dest=layer_name,target_layer={mask_lay_name},invert=no,dx=0,dy=0,size=5,x_anchor=0,y_anchor=0,rotation=0,mirror=none')
        return True
    
    def add_drill_sense_features(self):
        count = 1
        X_Pos = self.config["pth_hole_x_location"] + self.config["drill_sense_x_location_offset"]
        Y_Pos = self.config["pth_hole_y_location"] + self.config["drill_sense_y_location_offset"]
        for drill_lay in self.get_backdrill_info():
            # print(f"Processing Backdrill Layer: {drill_lay}")
            self.GENSTEP_CPN.workOnFirstLayer(layer_name=self.config["drill_sense_lay_name"],clear_layers=True)
            self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
            
            for lay in [drill_lay['drl_start'], drill_lay['drl_mnc']]:
                # print(f"Processing Span Start Layer: {lay}")
                if not self.GENJOB.layerExists(lay): continue
                # Add Pad and text on Start layer
                if lay == drill_lay['drl_start']:
                    self.GENSTEP_CPN.workOnFirstLayer(layer_name=lay,clear_layers=True)
                    self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
                    self.GENSTEP_CPN.COM(f'add_text,attributes=no,type=string,x={X_Pos-self.config["text_x"]/3},y={self.config["drill_sense_y_location_offset"]/2},text={count},x_size={self.config["text_x"]},y_size={self.config["text_y"]},w_factor={self.config["text_width_w_factor"]},polarity=positive,angle=0,mirror=no,fontname={self.config["font_type"]},ver=1')
                
                # Add Line on Must not cut layer
                if lay == drill_lay['drl_mnc']:
                    self.GENSTEP_CPN.workOnFirstLayer(layer_name=lay,clear_layers=True)
                    self.GENSTEP_CPN.COM(f'add_pad,attributes=no,x={X_Pos},y={Y_Pos},symbol=r{self.config["drill_sense_hole_pad_size"]},polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1')
                    self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={Y_Pos},xe={X_Pos},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')
                    self.GENSTEP_CPN.COM(f'add_line,attributes=no,xs={X_Pos},ys={self.config["pth_hole_y_location"]},xe={self.config["pth_hole_x_location"]},ye={self.config["pth_hole_y_location"]},symbol=r{self.config["connection_line_width"]},polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left')

            count += 1
            X_Pos += self.config["drill_sense_x_location_offset"]
        
        self.add_top_bot_text()
        self.add_top_bot_text(lay_name=BOT_LAYER_NAME, text="BOT", xPos=0.118, yPos=0.101, mirror="yes")
        self.add_profile_to_cpn()
        self.add_thieving()
        self.add_mask_openings(cu_lay_name=TOP_LAYER_NAME, mask_lay_name=TOP_MASK_NAME)
        self.add_mask_openings(cu_lay_name=BOT_LAYER_NAME, mask_lay_name=BOT_MASK_NAME)
        self.GENSTEP_CPN.workOnFirstLayer(layer_name=TOP_LAYER_NAME,clear_layers=True)

if __name__ == '__main__':
    dsbc = DepthSensingBackdrillCoupon(job_name=JOB)
    dsbc.add_clamping_hole_features()
    dsbc.add_drill_sense_features()
