#include "pch-c.h"
#ifndef _MSC_VER
# include <alloca.h>
#else
# include <malloc.h>
#endif


#include "codegen/il2cpp-codegen-metadata.h"





// 0x00000001 System.Single UnityEngine.WheelHit::get_forwardSlip()
extern void WheelHit_get_forwardSlip_m8F11089F49F1049C5D993A0E360E8738D7E600FC (void);
// 0x00000002 System.Single UnityEngine.WheelHit::get_sidewaysSlip()
extern void WheelHit_get_sidewaysSlip_m6AA5854F880C9BCDA98A22DBB694408954BB0CED (void);
// 0x00000003 System.Void UnityEngine.WheelCollider::set_motorTorque(System.Single)
extern void WheelCollider_set_motorTorque_mFE7962DF8003D10BA646545E56F0A6B3ED8803DA (void);
// 0x00000004 System.Void UnityEngine.WheelCollider::set_steerAngle(System.Single)
extern void WheelCollider_set_steerAngle_m1E46602E8B77EB747B1EA44D84B5EC99F86BB968 (void);
// 0x00000005 System.Boolean UnityEngine.WheelCollider::get_isGrounded()
extern void WheelCollider_get_isGrounded_m396F5249ED00A62F8C50403A7BB64CF5E649A61C (void);
// 0x00000006 System.Single UnityEngine.WheelCollider::get_rpm()
extern void WheelCollider_get_rpm_m5127D5BE0A627C29F38CFD8194C3F2470D8008B1 (void);
// 0x00000007 System.Void UnityEngine.WheelCollider::ConfigureVehicleSubsteps(System.Single,System.Int32,System.Int32)
extern void WheelCollider_ConfigureVehicleSubsteps_m3C0756B42ACAD0C05564B4C8EA0C48F4B70B2069 (void);
// 0x00000008 System.Void UnityEngine.WheelCollider::GetWorldPose(UnityEngine.Vector3&,UnityEngine.Quaternion&)
extern void WheelCollider_GetWorldPose_m227D45061C7734F3ED4A43B7F89605A398BE8BB5 (void);
// 0x00000009 System.Boolean UnityEngine.WheelCollider::GetGroundHit(UnityEngine.WheelHit&)
extern void WheelCollider_GetGroundHit_mDCD55AC74710E685DBA37F02C904B8F8F3E59DB9 (void);
static Il2CppMethodPointer s_methodPointers[9] = 
{
	WheelHit_get_forwardSlip_m8F11089F49F1049C5D993A0E360E8738D7E600FC,
	WheelHit_get_sidewaysSlip_m6AA5854F880C9BCDA98A22DBB694408954BB0CED,
	WheelCollider_set_motorTorque_mFE7962DF8003D10BA646545E56F0A6B3ED8803DA,
	WheelCollider_set_steerAngle_m1E46602E8B77EB747B1EA44D84B5EC99F86BB968,
	WheelCollider_get_isGrounded_m396F5249ED00A62F8C50403A7BB64CF5E649A61C,
	WheelCollider_get_rpm_m5127D5BE0A627C29F38CFD8194C3F2470D8008B1,
	WheelCollider_ConfigureVehicleSubsteps_m3C0756B42ACAD0C05564B4C8EA0C48F4B70B2069,
	WheelCollider_GetWorldPose_m227D45061C7734F3ED4A43B7F89605A398BE8BB5,
	WheelCollider_GetGroundHit_mDCD55AC74710E685DBA37F02C904B8F8F3E59DB9,
};
extern void WheelHit_get_forwardSlip_m8F11089F49F1049C5D993A0E360E8738D7E600FC_AdjustorThunk (void);
extern void WheelHit_get_sidewaysSlip_m6AA5854F880C9BCDA98A22DBB694408954BB0CED_AdjustorThunk (void);
static Il2CppTokenAdjustorThunkPair s_adjustorThunks[2] = 
{
	{ 0x06000001, WheelHit_get_forwardSlip_m8F11089F49F1049C5D993A0E360E8738D7E600FC_AdjustorThunk },
	{ 0x06000002, WheelHit_get_sidewaysSlip_m6AA5854F880C9BCDA98A22DBB694408954BB0CED_AdjustorThunk },
};
static const int32_t s_InvokerIndices[9] = 
{
	3912,
	3912,
	3348,
	3348,
	3904,
	3912,
	1444,
	1772,
	2823,
};
extern const CustomAttributesCacheGenerator g_UnityEngine_VehiclesModule_AttributeGenerators[];
IL2CPP_EXTERN_C const Il2CppCodeGenModule g_UnityEngine_VehiclesModule_CodeGenModule;
const Il2CppCodeGenModule g_UnityEngine_VehiclesModule_CodeGenModule = 
{
	"UnityEngine.VehiclesModule.dll",
	9,
	s_methodPointers,
	2,
	s_adjustorThunks,
	s_InvokerIndices,
	0,
	NULL,
	0,
	NULL,
	0,
	NULL,
	NULL,
	g_UnityEngine_VehiclesModule_AttributeGenerators,
	NULL, // module initializer,
	NULL,
	NULL,
	NULL,
};
